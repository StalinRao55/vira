"""
ai/providers/factory.py

Why this file exists:
    This is what makes "switching providers should require only a
    configuration change" (from the spec) literally true. Nothing outside
    this file decides which provider class to instantiate.

How it communicates with other modules:
    - Reads core/config.settings
    - Instantiates GeminiProvider / MockProvider (OpenAIProvider,
      AnthropicProvider, etc. plug in here in later passes)
    - Called from api/v1/dependencies.py to inject ILLMProvider into
      SendMessageUseCase
"""

from app.ai.providers.base import ILLMProvider
from app.ai.providers.gemini_provider import GeminiProvider
from app.ai.providers.mock_provider import MockProvider
from app.core.config import settings

_SUPPORTED_PROVIDERS = {"gemini", "mock"}  # extend as openai/anthropic/etc. are added


def get_llm_provider(provider_name: str | None = None) -> ILLMProvider:
    """Returns the configured provider. `provider_name` lets a request
    override the default (for the model selector dropdown in the UI);
    falls back to settings if not given."""
    name = provider_name or ("mock" if settings.environment == "test" else "gemini")

    if name not in _SUPPORTED_PROVIDERS:
        raise ValueError(f"Unsupported provider '{name}'. Supported: {_SUPPORTED_PROVIDERS}")

    if name == "gemini":
        return GeminiProvider(api_key=settings.gemini_api_key)
    if name == "mock":
        return MockProvider()

    raise ValueError(f"Unhandled provider '{name}'")  # unreachable, keeps type-checkers happy
