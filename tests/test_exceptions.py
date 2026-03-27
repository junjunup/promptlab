"""Tests for exception classes."""

from __future__ import annotations

from promptlab.exceptions import (
    ConfigError,
    EvaluationError,
    EvaluatorNotFoundError,
    PromptLabError,
    ProviderError,
    ProviderTimeoutError,
    RateLimitError,
)


class TestExceptions:
    """Tests for exception hierarchy."""

    def test_base_exception(self) -> None:
        e = PromptLabError("test error")
        assert str(e) == "test error"
        assert isinstance(e, Exception)

    def test_config_error(self) -> None:
        e = ConfigError("bad config")
        assert isinstance(e, PromptLabError)

    def test_provider_error_includes_provider_name(self) -> None:
        e = ProviderError("gpt4", "API failed")
        assert "gpt4" in str(e)
        assert "API failed" in str(e)
        assert e.provider == "gpt4"

    def test_timeout_is_provider_error(self) -> None:
        e = ProviderTimeoutError("gpt4", "timed out")
        assert isinstance(e, ProviderError)

    def test_rate_limit_is_provider_error(self) -> None:
        e = RateLimitError("gpt4", "rate limited")
        assert isinstance(e, ProviderError)

    def test_evaluation_error(self) -> None:
        e = EvaluationError("eval failed")
        assert isinstance(e, PromptLabError)

    def test_evaluator_not_found(self) -> None:
        e = EvaluatorNotFoundError("magic_eval")
        assert "magic_eval" in str(e)
        assert "Available" in str(e)
        assert e.evaluator_type == "magic_eval"
