"""LLM-as-Judge evaluator."""

from __future__ import annotations

from promptlab.evaluators.base import BaseEvaluator, EvalContext
from promptlab.models import AssertionResult

_DEFAULT_JUDGE_PROMPT = """\
You are an expert evaluator. Rate whether the following AI response \
adequately answers the question/task.

Task/Prompt:
{prompt}

AI Response:
{output}

{criteria}

Respond with ONLY "PASS" or "FAIL" followed by a brief explanation.
"""


class LlmJudgeEvaluator(BaseEvaluator):
    """Use another LLM to judge the quality of the output.

    Note: This evaluator requires an async provider to be injected
    at runtime by the Runner. The evaluate() method stores the config
    and the actual evaluation happens in evaluate_async().
    """

    def evaluate(self, ctx: EvalContext) -> AssertionResult:
        """Synchronous placeholder — returns a pending result.

        The actual LLM judge call is handled by the Runner via
        evaluate_async(). This method returns a skeleton result.

        Args:
            ctx: Evaluation context.

        Returns:
            AssertionResult marked as needing async evaluation.
        """
        # This is a placeholder; Runner handles the async call
        return AssertionResult(
            type="llm_judge",
            passed=False,
            message="LLM judge evaluation pending (requires async)",
        )

    def build_judge_prompt(self, ctx: EvalContext) -> str:
        """Build the judge prompt from context.

        Args:
            ctx: Evaluation context.

        Returns:
            Formatted judge prompt string.
        """
        criteria = ""
        if ctx.assertion.value:
            criteria = f"Evaluation criteria: {ctx.assertion.value}"

        judge_template = ctx.assertion.judge_prompt or _DEFAULT_JUDGE_PROMPT

        return judge_template.format(
            prompt=ctx.prompt_rendered,
            output=ctx.output,
            criteria=criteria,
        )

    def parse_judge_response(self, response: str) -> AssertionResult:
        """Parse the judge LLM's response into a result.

        Args:
            response: Raw text response from the judge LLM.

        Returns:
            AssertionResult based on judge verdict.
        """
        response_upper = response.strip().upper()
        passed = response_upper.startswith("PASS")

        return AssertionResult(
            type="llm_judge",
            passed=passed,
            actual=response.strip()[:200],
            message="" if passed else f"LLM judge verdict: FAIL — {response[:100]}",
        )
