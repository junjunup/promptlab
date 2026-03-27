"""Tests for Pydantic data models."""

from __future__ import annotations

import pytest

from promptlab.models import (
    AssertionConfig,
    AssertionType,
    EvalConfig,
    EvalRunResult,
    EvalSettings,
    PromptConfig,
    ProviderConfig,
    ProviderType,
    TestCaseConfig,
    TokenUsage,
)


class TestProviderConfig:
    """Tests for ProviderConfig model."""

    def test_defaults(self) -> None:
        cfg = ProviderConfig(id="test", type=ProviderType.OPENAI, model="gpt-4o-mini")
        assert cfg.temperature == 0.0
        assert cfg.max_tokens == 1024
        assert cfg.api_key is None

    def test_custom_values(self) -> None:
        cfg = ProviderConfig(
            id="custom",
            type=ProviderType.ANTHROPIC,
            model="claude-3",
            temperature=0.7,
            max_tokens=2048,
            api_key="sk-test",
        )
        assert cfg.temperature == 0.7
        assert cfg.api_key == "sk-test"


class TestAssertionConfig:
    """Tests for AssertionConfig model."""

    def test_contains_assertion(self) -> None:
        cfg = AssertionConfig(type=AssertionType.CONTAINS, value="hello")
        assert cfg.type == AssertionType.CONTAINS
        assert cfg.value == "hello"

    def test_cost_assertion(self) -> None:
        cfg = AssertionConfig(type=AssertionType.COST, max_tokens=500)
        assert cfg.max_tokens == 500

    def test_similarity_assertion(self) -> None:
        cfg = AssertionConfig(
            type=AssertionType.SIMILARITY, value="expected", threshold=0.9
        )
        assert cfg.threshold == 0.9


class TestTestCaseConfig:
    """Tests for TestCaseConfig model."""

    def test_with_alias(self) -> None:
        cfg = TestCaseConfig(
            vars={"q": "hello"},
            **{"assert": [AssertionConfig(type=AssertionType.CONTAINS, value="hi")]},
        )
        assert len(cfg.assert_) == 1

    def test_empty_vars(self) -> None:
        cfg = TestCaseConfig(**{"assert": []})
        assert cfg.vars == {}


class TestTokenUsage:
    """Tests for TokenUsage model."""

    def test_defaults(self) -> None:
        usage = TokenUsage()
        assert usage.prompt_tokens == 0
        assert usage.total_tokens == 0
        assert usage.estimated_cost_usd == 0.0

    def test_custom_values(self) -> None:
        usage = TokenUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            estimated_cost_usd=0.0015,
        )
        assert usage.total_tokens == 150


class TestEvalConfig:
    """Tests for EvalConfig model."""

    def test_minimal_config(self) -> None:
        cfg = EvalConfig(
            providers=[
                ProviderConfig(id="t", type=ProviderType.OPENAI, model="gpt-4o-mini")
            ],
            prompts=[PromptConfig(id="v1", content="test")],
            tests=[TestCaseConfig(**{"assert": []})],
        )
        assert cfg.description == ""
        assert cfg.settings.concurrency == 5

    def test_full_config(self) -> None:
        cfg = EvalConfig(
            description="Full test",
            providers=[
                ProviderConfig(id="a", type=ProviderType.OPENAI, model="gpt-4o-mini"),
                ProviderConfig(id="b", type=ProviderType.ANTHROPIC, model="claude-3"),
            ],
            prompts=[
                PromptConfig(id="v1", content="Q: {{q}}"),
                PromptConfig(id="v2", content="Answer: {{q}}"),
            ],
            tests=[
                TestCaseConfig(
                    vars={"q": "hello"},
                    **{
                        "assert": [
                            AssertionConfig(type=AssertionType.CONTAINS, value="hi"),
                        ]
                    },
                ),
            ],
            settings=EvalSettings(concurrency=10, timeout=60),
        )
        assert len(cfg.providers) == 2
        assert len(cfg.prompts) == 2
        assert cfg.settings.concurrency == 10


class TestEvalRunResult:
    """Tests for EvalRunResult model."""

    def test_defaults(self) -> None:
        result = EvalRunResult(run_id="test123")
        assert result.total_tests == 0
        assert result.results == []
        assert result.timestamp > 0

    def test_model_dump(self) -> None:
        result = EvalRunResult(
            run_id="test123",
            total_tests=5,
            total_passed=3,
            total_failed=2,
            overall_pass_rate=0.6,
        )
        data = result.model_dump()
        assert data["run_id"] == "test123"
        assert data["overall_pass_rate"] == 0.6
