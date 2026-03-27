"""PromptLab exception hierarchy."""

from __future__ import annotations


class PromptLabError(Exception):
    """Base exception for all PromptLab errors."""


class ConfigError(PromptLabError):
    """Raised when the configuration file is invalid or cannot be parsed."""


class ProviderError(PromptLabError):
    """Raised when an LLM provider call fails."""

    def __init__(self, provider: str, message: str) -> None:
        self.provider = provider
        super().__init__(f"[{provider}] {message}")


class ProviderTimeoutError(ProviderError):
    """Raised when an LLM provider call times out."""


class RateLimitError(ProviderError):
    """Raised when an LLM provider returns a rate limit error."""


class EvaluationError(PromptLabError):
    """Raised when an evaluation fails to execute."""


class EvaluatorNotFoundError(PromptLabError):
    """Raised when a referenced evaluator does not exist."""

    def __init__(self, evaluator_type: str) -> None:
        self.evaluator_type = evaluator_type
        super().__init__(
            f"Unknown evaluator type: '{evaluator_type}'. "
            f"Available: exact, contains, regex, json_valid, similarity, "
            f"llm_judge, cost"
        )
