"""Tests for provider registry and base classes."""

from __future__ import annotations

import pytest

from promptlab.models import ProviderConfig, ProviderType
from promptlab.providers.base import BaseProvider, ProviderResponse
from promptlab.providers.registry import create_provider, get_provider_class


class TestProviderRegistry:
    """Tests for provider registry."""

    def test_get_openai_class(self) -> None:
        from promptlab.providers.openai import OpenAIProvider

        cls = get_provider_class(ProviderType.OPENAI)
        assert cls is OpenAIProvider

    def test_get_anthropic_class(self) -> None:
        from promptlab.providers.anthropic import AnthropicProvider

        cls = get_provider_class(ProviderType.ANTHROPIC)
        assert cls is AnthropicProvider

    def test_get_ollama_class(self) -> None:
        from promptlab.providers.ollama import OllamaProvider

        cls = get_provider_class(ProviderType.OLLAMA)
        assert cls is OllamaProvider

    def test_create_openai_provider(self) -> None:
        config = ProviderConfig(
            id="test", type=ProviderType.OPENAI, model="gpt-4o-mini"
        )
        provider = create_provider(config)
        assert provider.id == "test"
        assert provider.model == "gpt-4o-mini"

    def test_create_ollama_provider(self) -> None:
        config = ProviderConfig(id="local", type=ProviderType.OLLAMA, model="llama3")
        provider = create_provider(config)
        assert provider.id == "local"


class TestProviderResponse:
    """Tests for ProviderResponse dataclass."""

    def test_default_values(self) -> None:
        resp = ProviderResponse(text="hello")
        assert resp.text == "hello"
        assert resp.latency_ms == 0.0
        assert resp.token_usage.total_tokens == 0

    def test_with_values(self) -> None:
        from promptlab.models import TokenUsage

        usage = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        resp = ProviderResponse(text="world", token_usage=usage, latency_ms=100.0)
        assert resp.token_usage.total_tokens == 15
        assert resp.latency_ms == 100.0
