"""OpenAI provider adapter."""

from __future__ import annotations

from promptlab.exceptions import ProviderError, ProviderTimeoutError, RateLimitError
from promptlab.models import ProviderConfig, TokenUsage
from promptlab.providers.base import BaseProvider, ProviderResponse

# Pricing per 1M tokens (USD) — updated March 2026
_OPENAI_PRICING: dict[str, tuple[float, float]] = {
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-3.5-turbo": (0.50, 1.50),
    "o1": (15.00, 60.00),
    "o1-mini": (3.00, 12.00),
    "o3-mini": (1.10, 4.40),
}


class OpenAIProvider(BaseProvider):
    """OpenAI API provider."""

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self._client: object | None = None

    def _get_client(self) -> object:
        """Lazy-initialize the OpenAI async client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
            except ImportError as e:
                raise ProviderError(
                    self.id,
                    "openai package not installed. "
                    "Install with: pip install promptlab[openai]",
                ) from e

            kwargs: dict[str, object] = {}
            if self.config.api_key:
                kwargs["api_key"] = self.config.api_key
            if self.config.base_url:
                kwargs["base_url"] = self.config.base_url

            self._client = AsyncOpenAI(**kwargs)
        return self._client  # type: ignore[return-value]

    async def complete(self, prompt: str) -> ProviderResponse:
        """Call OpenAI chat completion API.

        Args:
            prompt: The rendered prompt text.

        Returns:
            ProviderResponse with text and token usage.
        """
        client = self._get_client()

        try:
            response = await client.chat.completions.create(  # type: ignore[union-attr]
                model=self.config.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
        except Exception as e:
            error_msg = str(e).lower()
            if "timeout" in error_msg:
                raise ProviderTimeoutError(self.id, str(e)) from e
            if "rate" in error_msg and "limit" in error_msg:
                raise RateLimitError(self.id, str(e)) from e
            raise ProviderError(self.id, str(e)) from e

        text = response.choices[0].message.content or ""  # type: ignore[union-attr]
        usage = response.usage  # type: ignore[union-attr]

        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0
        total_tokens = prompt_tokens + completion_tokens

        # Calculate cost
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
    pricing = _OPENAI_PRICING.get(model)
    if pricing is None:
        # Try prefix match for versioned models
        for key, val in _OPENAI_PRICING.items():
            if model.startswith(key):
                pricing = val
                break

    if pricing is None:
        return 0.0

    input_price, output_price = pricing
    cost = (prompt_tokens * input_price + completion_tokens * output_price) / 1_000_000
    return round(cost, 8)
