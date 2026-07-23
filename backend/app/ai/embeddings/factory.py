"""
ai/embeddings/factory.py

Why this file exists:
    Same rationale as ai/providers/factory.py — the single place that
    decides which concrete IEmbeddingProvider to instantiate based on
    config, so nothing else in the codebase imports a concrete provider.
"""

from app.ai.embeddings.base import IEmbeddingProvider
from app.ai.embeddings.gemini_embedding_provider import GeminiEmbeddingProvider
from app.ai.embeddings.mock_embedding_provider import MockEmbeddingProvider
from app.core.config import settings


def get_embedding_provider(provider_name: str | None = None) -> IEmbeddingProvider:
    name = provider_name or ("mock" if settings.environment == "test" else "gemini")
    if name == "gemini":
        return GeminiEmbeddingProvider(api_key=settings.gemini_api_key)
    if name == "mock":
        return MockEmbeddingProvider()
    raise ValueError(f"Unsupported embedding provider '{name}'")
