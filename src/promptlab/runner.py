"""Core evaluation runner — orchestrates the entire eval pipeline."""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

from jinja2 import Template

from promptlab.evaluators import create_evaluator
from promptlab.evaluators.base import EvalContext
from promptlab.evaluators.llm_judge import LlmJudgeEvaluator
from promptlab.exceptions import ProviderError
from promptlab.models import (
    AssertionConfig,
    AssertionResult,
    AssertionType,
    EvalConfig,
    EvalRunResult,
    ProviderSummary,
    TestResult,
    TokenUsage,
)
from promptlab.providers import create_provider
from promptlab.providers.base import BaseProvider


class Runner:
    """Evaluation runner that orchestrates the entire eval pipeline.

    Flow:
        1. Initialize providers from config
        2. For each (test, prompt, provider) combination:
           a. Render the prompt template with test variables
           b. Call the LLM provider
           c. Run all assertions/evaluators on the output
           d. Record the result
        3. Aggregate results and produce the final report
    """

    def __init__(self, config: EvalConfig, config_path: str = "") -> None:
        self.config = config
        self.config_path = config_path
        self.providers: dict[str, BaseProvider] = {}
        self._results: list[TestResult] = []

    async def run(self) -> dict[str, Any]:
        """Execute the full evaluation pipeline.

        Returns:
            Evaluation results as a dictionary.
        """
        start_time = time.perf_counter()
        run_id = uuid.uuid4().hex[:12]

        # Initialize providers
        for provider_config in self.config.providers:
            provider = create_provider(provider_config)
            self.providers[provider_config.id] = provider

        # Build all evaluation tasks
        tasks: list[tuple[int, str, str]] = []
        for test_idx, _test in enumerate(self.config.tests):
            for prompt in self.config.prompts:
                for provider_config in self.config.providers:
                    tasks.append((test_idx, prompt.id, provider_config.id))

        # Run evaluations with concurrency control
        semaphore = asyncio.Semaphore(self.config.settings.concurrency)

        async def bounded_eval(
            test_idx: int, prompt_id: str, provider_id: str
        ) -> TestResult:
            async with semaphore:
                return await self._evaluate_single(test_idx, prompt_id, provider_id)

        results = await asyncio.gather(
            *[bounded_eval(t, p, pv) for t, p, pv in tasks],
            return_exceptions=True,
        )

        # Collect results, handling exceptions
        for result in results:
            if isinstance(result, Exception):
                self._results.append(
                    TestResult(
                        test_index=-1,
                        provider_id="unknown",
                        prompt_id="unknown",
                        prompt_rendered="",
                        output="",
                        assertions=[],
                        passed=False,
                        error=str(result),
                    )
                )
            else:
                self._results.append(result)

        duration_ms = (time.perf_counter() - start_time) * 1000

        # Build the final result
        eval_result = self._build_eval_result(run_id, duration_ms)

        return eval_result.model_dump()

    async def _evaluate_single(
        self, test_idx: int, prompt_id: str, provider_id: str
    ) -> TestResult:
        """Evaluate a single (test, prompt, provider) combination.

        Args:
            test_idx: Index of the test case.
            prompt_id: ID of the prompt template.
            provider_id: ID of the provider.

        Returns:
            TestResult for this combination.
        """
        test = self.config.tests[test_idx]
        prompt_config = next(p for p in self.config.prompts if p.id == prompt_id)
        provider = self.providers[provider_id]

        # Render the prompt template
        try:
            template = Template(prompt_config.content)
            rendered = template.render(**test.vars)
        except Exception as e:
            return TestResult(
                test_index=test_idx,
                test_description=test.description,
                provider_id=provider_id,
                prompt_id=prompt_id,
                prompt_rendered=prompt_config.content,
                output="",
                assertions=[],
                passed=False,
                error=f"Template rendering failed: {e}",
            )

        # Call the LLM
        token_usage: TokenUsage | None = None
        output = ""
        error: str | None = None
        latency_ms = 0.0

        try:
            response = await provider.timed_complete(rendered)
            output = response.text
            token_usage = response.token_usage
            latency_ms = response.latency_ms
        except ProviderError as e:
            error = str(e)
            output = ""
        except Exception as e:
            error = f"Unexpected error: {e}"
            output = ""

        # Run assertions
        assertion_results: list[AssertionResult] = []

        if error is None:
            for assertion_config in test.assert_:
                if assertion_config.type == AssertionType.COST:
                    # Cost evaluator uses token count as output
                    total_tokens = str(token_usage.total_tokens if token_usage else 0)
                    ctx = EvalContext(
                        output=total_tokens,
                        assertion=assertion_config,
                        prompt_rendered=rendered,
                        variables=test.vars,
                    )
                elif assertion_config.type == AssertionType.LLM_JUDGE:
                    # LLM judge needs async handling
                    result = await self._run_llm_judge(
                        assertion_config, rendered, output
                    )
                    assertion_results.append(result)
                    continue
                else:
                    ctx = EvalContext(
                        output=output,
                        assertion=assertion_config,
                        prompt_rendered=rendered,
                        variables=test.vars,
                    )

                evaluator = create_evaluator(assertion_config.type)
                result = evaluator.evaluate(ctx)
                assertion_results.append(result)

        all_passed = (
            all(r.passed for r in assertion_results)
            if assertion_results
            else error is None
        )

        # Generate test description
        description = test.description
        if not description:
            first_var = next(iter(test.vars.values()), "")
            description = first_var[:60] + "..." if len(first_var) > 60 else first_var

        return TestResult(
            test_index=test_idx,
            test_description=description,
            provider_id=provider_id,
            prompt_id=prompt_id,
            prompt_rendered=rendered,
            output=output,
            assertions=assertion_results,
            passed=all_passed,
            latency_ms=latency_ms,
            token_usage=token_usage,
            error=error,
        )

    async def _run_llm_judge(
        self,
        assertion_config: AssertionConfig,
        rendered_prompt: str,
        output: str,
    ) -> AssertionResult:
        """Run the LLM-as-Judge evaluator asynchronously.

        Args:
            assertion_config: The assertion config for the judge.
            rendered_prompt: The rendered prompt that produced the output.
            output: The LLM output to judge.

        Returns:
            AssertionResult from the judge.
        """
        judge_evaluator = LlmJudgeEvaluator()
        ctx = EvalContext(
            output=output,
            assertion=assertion_config,
            prompt_rendered=rendered_prompt,
        )

        judge_prompt = judge_evaluator.build_judge_prompt(ctx)

        # Determine which provider to use for judging
        judge_provider_id = assertion_config.judge_provider
        if judge_provider_id and judge_provider_id in self.providers:
            judge_provider = self.providers[judge_provider_id]
        else:
            # Use the first provider as default judge
            judge_provider = next(iter(self.providers.values()))

        try:
            response = await judge_provider.timed_complete(judge_prompt)
            return judge_evaluator.parse_judge_response(response.text)
        except ProviderError as e:
            return AssertionResult(
                type="llm_judge",
                passed=False,
                message=f"LLM judge failed: {e}",
            )

    def _build_eval_result(self, run_id: str, duration_ms: float) -> EvalRunResult:
        """Build the final evaluation result with summaries.

        Args:
            run_id: Unique run identifier.
            duration_ms: Total duration in milliseconds.

        Returns:
            Complete EvalRunResult.
        """
        # Per-provider summaries
        provider_map: dict[str, list[TestResult]] = {}
        for result in self._results:
            provider_map.setdefault(result.provider_id, []).append(result)

        summaries: list[ProviderSummary] = []
        for provider_id, results in provider_map.items():
            passed = sum(1 for r in results if r.passed)
            failed = len(results) - passed
            total_tokens = sum(
                r.token_usage.total_tokens for r in results if r.token_usage
            )
            total_cost = sum(
                r.token_usage.estimated_cost_usd for r in results if r.token_usage
            )
            avg_latency = (
                sum(r.latency_ms for r in results) / len(results) if results else 0.0
            )

            summaries.append(
                ProviderSummary(
                    provider_id=provider_id,
                    total_tests=len(results),
                    passed=passed,
                    failed=failed,
                    pass_rate=passed / len(results) if results else 0.0,
                    total_tokens=total_tokens,
                    total_cost_usd=total_cost,
                    avg_latency_ms=avg_latency,
                )
            )

        total_passed = sum(1 for r in self._results if r.passed)
        total_failed = len(self._results) - total_passed
        total_cost = sum(s.total_cost_usd for s in summaries)

        return EvalRunResult(
            run_id=run_id,
            description=self.config.description,
            config_path=self.config_path,
            results=self._results,
            provider_summaries=summaries,
            total_tests=len(self._results),
            total_passed=total_passed,
            total_failed=total_failed,
            overall_pass_rate=(
                total_passed / len(self._results) if self._results else 0.0
            ),
            total_cost_usd=total_cost,
            total_duration_ms=duration_ms,
        )
