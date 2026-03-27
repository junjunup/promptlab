"""Anthropic provider adapter."""

from __future__ import annotations

from promptlab.exceptions import ProviderError, ProviderTimeoutError, RateLimitError
from promptlab.models import ProviderConfig, TokenUsage
from promptlab.providers.base import BaseProvider, ProviderResponse

# Pricing per 1M tokens (USD) — updated March 2026
_ANTHROPIC_PRICING: dict[str, tuple[float, float]] = {
    "claude-3-5-sonnet": (3.00, 15.00),
    "claude-3-5-haiku": (0.80, 4.00),
    "claude-3-opus": (15.00, 75.00),
    "claude-3-haiku": (0.25, 1.25),
    "claude-3-sonnet": (3.00, 15.00),
}


class AnthropicProvider(BaseProvider):
    """Anthropic API provider."""

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self._client: object | None = None

    def _get_client(self) -> object:
        """Lazy-initialize the Anthropic async client."""
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
            except ImportError as e:
                raise ProviderError(
                    self.id,
                    "anthropic package not installed. "
                    "Install with: pip install promptlab[anthropic]",
                ) from e

            kwargs: dict[str, object] = {}
            if self.config.api_key:
                kwargs["api_key"] = self.config.api_key
            if self.config.base_url:
                kwargs["base_url"] = self.config.base_url

            self._client = AsyncAnthropic(**kwargs)
        return self._client  # type: ignore[return-value]

    async def complete(self, prompt: str) -> ProviderResponse:
        """Call Anthropic messages API.

        Args:
            prompt: The rendered prompt text.

        Returns:
            ProviderResponse with text and token usage.
        """
        client = self._get_client()

        try:
            response = await client.messages.create(  # type: ignore[union-attr]
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.temperature,
            )
        except Exception as e:
            error_msg = str(e).lower()
            if "timeout" in error_msg:
                raise ProviderTimeoutError(self.id, str(e)) from e
            if "rate" in error_msg:
                raise RateLimitError(self.id, str(e)) from e
            raise ProviderError(self.id, str(e)) from e

        text = ""
        for block in response.content:  # type: ignore[union-attr]
            if hasattr(block, "text"):
                text += block.text

        usage = response.usage  # type: ignore[union-attr]
        prompt_tokens = usage.input_tokens if usage else 0
        completion_tokens = usage.output_tokens if usage else 0
        total_tokens = prompt_tokens + completion_tokens

        cost = _estimate_cost(self.config.model, prompt_tokens, completion_tokens)

        token_usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=cost,
        )

        return ProviderResponse(
            text=text.strip(),
            token_usage=token_usage,
            raw_response=response,
        )


def _estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Estimate cost in USD based on model pricing."""
    pricing = _ANTHROPIC_PRICING.get(model)
    if pricing is None:
        for key, val in _ANTHROPIC_PRICING.items():
            if model.startswith(key):
                pricing = val
                break

    if pricing is None:
        return 0.0

    input_price, output_price = pricing
    cost = (prompt_tokens * input_price + completion_tokens * output_price) / 1_000_000
    return round(cost, 8)
