"""Tests for the evaluation runner."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from promptlab.models import (
    AssertionConfig,
    AssertionType,
    EvalConfig,
    EvalSettings,
    PromptConfig,
    ProviderConfig,
    ProviderType,
    TestCaseConfig,
    TokenUsage,
)
from promptlab.providers.base import ProviderResponse
from promptlab.runner import Runner


def _make_config(
    num_tests: int = 2,
    num_prompts: int = 1,
    num_providers: int = 1,
) -> EvalConfig:
    """Helper to create test configs."""
    providers = [
        ProviderConfig(
            id=f"provider-{i}",
            type=ProviderType.OPENAI,
            model="gpt-4o-mini",
        )
        for i in range(num_providers)
    ]
    prompts = [
        PromptConfig(id=f"prompt-{i}", content="Q: {{question}}")
        for i in range(num_prompts)
    ]
    tests = [
        TestCaseConfig(
            vars={"question": f"Test question {i}"},
            **{
                "assert": [
                    AssertionConfig(type=AssertionType.CONTAINS, value=f"answer{i}"),
                ]
            },
        )
        for i in range(num_tests)
    ]
    return EvalConfig(
        description="Runner test",
        providers=providers,
        prompts=prompts,
        tests=tests,
        settings=EvalSettings(concurrency=2, timeout=10),
    )


class TestRunner:
    """Tests for the evaluation runner."""

    @pytest.mark.asyncio
    async def test_run_basic(self) -> None:
        """Test basic runner execution with mocked provider."""
        config = _make_config(num_tests=2, num_prompts=1, num_providers=1)

        mock_response = ProviderResponse(
            text="The answer0 is here",
            token_usage=TokenUsage(
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15,
                estimated_cost_usd=0.001,
            ),
        )

        with patch("promptlab.runner.create_provider") as mock_create:
            mock_provider = AsyncMock()
            mock_provider.timed_complete = AsyncMock(return_value=mock_response)
            mock_provider.id = "provider-0"
            mock_create.return_value = mock_provider

            runner = Runner(config)
            results = await runner.run()

        assert results["total_tests"] == 2
        assert results["total_passed"] >= 1  # First test should pass
        assert results["total_cost_usd"] > 0
        assert len(results["results"]) == 2
        assert len(results["provider_summaries"]) == 1

    @pytest.mark.asyncio
    async def test_run_multi_provider(self) -> None:
        """Test runner with multiple providers."""
        config = _make_config(num_tests=1, num_prompts=1, num_providers=2)

        mock_response = ProviderResponse(
            text="answer0",
            token_usage=TokenUsage(total_tokens=10),
        )

        with patch("promptlab.runner.create_provider") as mock_create:
            mock_provider = AsyncMock()
            mock_provider.timed_complete = AsyncMock(return_value=mock_response)
            mock_create.return_value = mock_provider

            runner = Runner(config)
            results = await runner.run()

        assert results["total_tests"] == 2  # 1 test * 1 prompt * 2 providers
        assert len(results["provider_summaries"]) == 2

    @pytest.mark.asyncio
    async def test_run_multi_prompt(self) -> None:
        """Test runner with multiple prompts."""
        config = _make_config(num_tests=1, num_prompts=2, num_providers=1)

        mock_response = ProviderResponse(
            text="answer0",
            token_usage=TokenUsage(total_tokens=10),
        )

        with patch("promptlab.runner.create_provider") as mock_create:
            mock_provider = AsyncMock()
            mock_provider.timed_complete = AsyncMock(return_value=mock_response)
            mock_create.return_value = mock_provider

            runner = Runner(config)
            results = await runner.run()

        assert results["total_tests"] == 2  # 1 test * 2 prompts * 1 provider

    @pytest.mark.asyncio
    async def test_run_provider_error_handled(self) -> None:
        """Test that provider errors are handled gracefully."""
        config = _make_config(num_tests=1)

        with patch("promptlab.runner.create_provider") as mock_create:
            mock_provider = AsyncMock()
            mock_provider.timed_complete = AsyncMock(side_effect=Exception("API error"))
            mock_create.return_value = mock_provider

            runner = Runner(config)
            results = await runner.run()

        # Should still produce results, but with errors
        assert results["total_tests"] == 1
        assert results["results"][0]["error"] is not None

    @pytest.mark.asyncio
    async def test_run_template_rendering(self) -> None:
        """Test that Jinja2 templates are rendered correctly."""
        config = EvalConfig(
            description="Template test",
            providers=[
                ProviderConfig(
                    id="test",
                    type=ProviderType.OPENAI,
                    model="gpt-4o-mini",
                ),
            ],
            prompts=[
                PromptConfig(
                    id="v1",
                    content="Name: {{name}}, Age: {{age}}",
                ),
            ],
            tests=[
                TestCaseConfig(
                    vars={"name": "Alice", "age": "30"},
                    **{
                        "assert": [
                            AssertionConfig(type=AssertionType.CONTAINS, value="Alice"),
                        ]
                    },
                ),
            ],
            settings=EvalSettings(concurrency=1),
        )

        mock_response = ProviderResponse(
            text="Name: Alice, Age: 30",
            token_usage=TokenUsage(total_tokens=10),
        )

        with patch("promptlab.runner.create_provider") as mock_create:
            mock_provider = AsyncMock()
            mock_provider.timed_complete = AsyncMock(return_value=mock_response)
            mock_create.return_value = mock_provider

            runner = Runner(config)
            results = await runner.run()

        assert results["total_passed"] == 1
        rendered = results["results"][0]["prompt_rendered"]
        assert "Alice" in rendered
        assert "30" in rendered

    @pytest.mark.asyncio
    async def test_run_cost_assertion(self) -> None:
        """Test cost assertion evaluator integration."""
        config = EvalConfig(
            description="Cost test",
            providers=[
                ProviderConfig(
                    id="test", type=ProviderType.OPENAI, model="gpt-4o-mini"
                ),
            ],
            prompts=[
                PromptConfig(id="v1", content="{{question}}"),
            ],
            tests=[
                TestCaseConfig(
                    vars={"question": "Hello"},
                    **{
                        "assert": [
                            AssertionConfig(type=AssertionType.COST, max_tokens=100),
                        ]
                    },
                ),
            ],
            settings=EvalSettings(concurrency=1),
        )

        mock_response = ProviderResponse(
            text="Hi",
            token_usage=TokenUsage(total_tokens=50),
        )

        with patch("promptlab.runner.create_provider") as mock_create:
            mock_provider = AsyncMock()
            mock_provider.timed_complete = AsyncMock(return_value=mock_response)
            mock_create.return_value = mock_provider

            runner = Runner(config)
            results = await runner.run()

        assert results["total_passed"] == 1

    @pytest.mark.asyncio
    async def test_run_result_structure(self) -> None:
        """Test that result dictionary has expected keys."""
        config = _make_config(num_tests=1)

        mock_response = ProviderResponse(
            text="answer0",
            token_usage=TokenUsage(total_tokens=10, estimated_cost_usd=0.001),
        )

        with patch("promptlab.runner.create_provider") as mock_create:
            mock_provider = AsyncMock()
            mock_provider.timed_complete = AsyncMock(return_value=mock_response)
            mock_create.return_value = mock_provider

            runner = Runner(config)
            results = await runner.run()

        assert "run_id" in results
        assert "timestamp" in results
        assert "results" in results
        assert "provider_summaries" in results
        assert "total_tests" in results
        assert "total_passed" in results
        assert "total_failed" in results
        assert "overall_pass_rate" in results
        assert "total_cost_usd" in results
        assert "total_duration_ms" in results
