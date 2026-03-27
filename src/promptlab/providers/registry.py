"""Provider registry — maps provider types to implementation classes."""

from __future__ import annotations

from promptlab.exceptions import ProviderError
from promptlab.models import ProviderConfig, ProviderType
from promptlab.providers.base import BaseProvider


def get_provider_class(provider_type: ProviderType) -> type[BaseProvider]:
    """Get the provider class for a given provider type.

    Args:
        provider_type: The provider type enum.

    Returns:
        The provider class.

    Raises:
        ProviderError: If the provider type is unsupported.
    """
    match provider_type:
        case ProviderType.OPENAI:
            from promptlab.providers.openai import OpenAIProvider

            return OpenAIProvider
        case ProviderType.ANTHROPIC:
            from promptlab.providers.anthropic import AnthropicProvider

            return AnthropicProvider
        case ProviderType.OLLAMA:
            from promptlab.providers.ollama import OllamaProvider

            return OllamaProvider
        case _:
            raise ProviderError(
                "registry", f"Unsupported provider type: {provider_type}"
            )


def create_provider(config: ProviderConfig) -> BaseProvider:
    """Create a provider instance from config.

    Args:
        config: Provider configuration.

    Returns:
        Initialized provider instance.
    """
    cls = get_provider_class(config.type)
    return cls(config)
