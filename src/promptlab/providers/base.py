"""Base class for LLM providers."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from promptlab.models import ProviderConfig, TokenUsage


@dataclass
class ProviderResponse:
    """Response from an LLM provider."""

    text: str
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    latency_ms: float = 0.0
    raw_response: object = None


class BaseProvider(ABC):
    """Abstract base class for LLM providers.

    All provider implementations must inherit from this class and implement
    the `complete` method.
    """

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config
        self.id = config.id
        self.model = config.model

    @abstractmethod
    async def complete(self, prompt: str) -> ProviderResponse:
        """Send a prompt to the LLM and return the response.

        Args:
            prompt: The rendered prompt text.

        Returns:
            ProviderResponse with text, token usage, and latency.

        Raises:
            ProviderError: If the API call fails.
            ProviderTimeoutError: If the call times out.
            RateLimitError: If rate limited.
        """

    async def timed_complete(self, prompt: str) -> ProviderResponse:
        """Call complete() with automatic latency measurement.

        Args:
            prompt: The rendered prompt text.

        Returns:
            ProviderResponse with latency_ms populated.
        """
        start = time.perf_counter()
        response = await self.complete(prompt)
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.latency_ms = elapsed_ms
        return response

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id!r} model={self.model!r}>"
