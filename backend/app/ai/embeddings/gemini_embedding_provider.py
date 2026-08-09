"""
ai/embeddings/gemini_embedding_provider.py

Why this file exists:
    Concrete IEmbeddingProvider using Google's text-embedding endpoint. The
    only file that knows Gemini's embedding request/response shape.

How it communicates with other modules:
    - Implements ai/embeddings/base.IEmbeddingProvider
    - Instantiated by ai/embeddings/factory.py
"""

import httpx

from app.ai.embeddings.base import IEmbeddingProvider

_EMBED_MODEL = "gemini-embedding-001"
_EMBED_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{_EMBED_MODEL}:embedContent"
_BATCH_EMBED_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{_EMBED_MODEL}:batchEmbedContents"


class GeminiEmbeddingProvider(IEmbeddingProvider):
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Gemini API key is not configured (GEMINI_API_KEY)")
        self._api_key = api_key

    @property
    def dimensions(self) -> int:
        return 3072  # gemini-embedding-001 output size (this account returns 3072)

    async def embed(self, text: str) -> list[float]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                _EMBED_URL,
                params={"key": self._api_key},
                json={"model": f"models/{_EMBED_MODEL}", "content": {"parts": [{"text": text}]}},
            )
            if response.status_code >= 400:
                raise RuntimeError(
                    f"Gemini embedding failed (HTTP {response.status_code}): {response.text}"
                )
            return response.json()["embedding"]["values"]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        requests = [
            {"model": f"models/{_EMBED_MODEL}", "content": {"parts": [{"text": t}]}} for t in texts
        ]
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                _BATCH_EMBED_URL,
                params={"key": self._api_key},
                json={"requests": requests},
            )
            if response.status_code >= 400:
                raise RuntimeError(
                    f"Gemini batch embedding failed (HTTP {response.status_code}): {response.text}"
                )
            return [e["values"] for e in response.json()["embeddings"]]
