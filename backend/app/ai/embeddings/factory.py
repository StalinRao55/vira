"""
ai/embeddings/factory.py

Why this file exists:
    Same rationale as ai/providers/factory.py — the single place that
    decides which concrete IEmbeddingProvider to instantiate based on
    config, so nothing else in the codebase imports a concrete provider.
"""

import logging

from app.ai.embeddings.base import IEmbeddingProvider
from app.ai.embeddings.gemini_embedding_provider import GeminiEmbeddingProvider
from app.ai.embeddings.mock_embedding_provider import MockEmbeddingProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

_GEMINI_MODELS_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def _has_valid_api_key() -> bool:
    """True only if a gemini key is set AND it is not the placeholder AND
    it is accepted by Google. The network check runs once per process (the
    caller caches via the returned provider selection)."""
    if not settings.gemini_api_key or settings.gemini_api_key == "your_gemini_api_key":
        return False
    return _gemini_key_accepts_config()


def _gemini_key_accepts_config() -> bool:
    """Verify the key is usable by calling the lightweight models list
    endpoint. A leaked/revoked/invalid key returns 4xx, in which case we
    fall back to mock instead of crashing at chat time."""
    try:
        import httpx

        with httpx.Client(timeout=10.0) as client:
            resp = client.get(_GEMINI_MODELS_URL, params={"key": settings.gemini_api_key})
            if resp.status_code == 200:
                return True
            logger.warning(
                "GEMINI_API_KEY rejected by Gemini API (HTTP %s): %s — falling back to MockEmbeddingProvider",
                resp.status_code,
                resp.json().get("error", {}).get("message", resp.text[:200]),
            )
            return False
    except Exception as exc:  # noqa: BLE001 - network/parse errors must not crash selection
        logger.warning(
            "Could not validate GEMINI_API_KEY with Gemini API (%s) — falling back to MockEmbeddingProvider", exc
        )
        return False


def get_embedding_provider(provider_name: str | None = None) -> IEmbeddingProvider:
    name = provider_name or ("mock" if settings.environment == "test" else "gemini")
    # Auto-fallback to mock when no valid API key is configured (development/demo mode)
    if name == "gemini" and not _has_valid_api_key():
        logger.warning("No valid GEMINI_API_KEY found — falling back to MockEmbeddingProvider")
        return MockEmbeddingProvider()
    if name == "gemini":
        return GeminiEmbeddingProvider(api_key=settings.gemini_api_key)
    if name == "mock":
        return MockEmbeddingProvider()
    raise ValueError(f"Unsupported embedding provider '{name}'")
