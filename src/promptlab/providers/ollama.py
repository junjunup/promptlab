"""Ollama (local) provider adapter."""

from __future__ import annotations

import httpx

from promptlab.exceptions import ProviderError, ProviderTimeoutError
from promptlab.models import ProviderConfig, TokenUsage
from promptlab.providers.base import BaseProvider, ProviderResponse

_DEFAULT_OLLAMA_URL = "http://localhost:11434"


class OllamaProvider(BaseProvider):
    """Ollama local model provider (uses HTTP API directly)."""

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self.base_url = config.base_url or _DEFAULT_OLLAMA_URL

    async def complete(self, prompt: str) -> ProviderResponse:
        """Call Ollama chat API.

        Args:
            prompt: The rendered prompt text.

        Returns:
            ProviderResponse with text and estimated token usage.
        """
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
        except httpx.TimeoutException as e:
            raise ProviderTimeoutError(self.id, f"Ollama request timed out: {e}") from e
        except httpx.HTTPError as e:
            raise ProviderError(self.id, f"Ollama request failed: {e}") from e

        data = resp.json()
        text = data.get("message", {}).get("content", "")

        # Ollama provides eval_count and prompt_eval_count
        prompt_tokens = data.get("prompt_eval_count", 0)
        completion_tokens = data.get("eval_count", 0)
        total_tokens = prompt_tokens + completion_tokens

        token_usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=0.0,  # Local models are free
        )

        return ProviderResponse(
            text=text.strip(),
            token_usage=token_usage,
            raw_response=data,
        )
