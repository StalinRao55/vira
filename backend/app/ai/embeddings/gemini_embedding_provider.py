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

_EMBED_URL = "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent"
_BATCH_EMBED_URL = "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:batchEmbedContents"


class GeminiEmbeddingProvider(IEmbeddingProvider):
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Gemini API key is not configured (GEMINI_API_KEY)")
        self._api_key = api_key

    @property
    def dimensions(self) -> int:
        return 768  # text-embedding-004 output size

    async def embed(self, text: str) -> list[float]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                _EMBED_URL,
                params={"key": self._api_key},
                json={"content": {"parts": [{"text": text}]}},
            )
            response.raise_for_status()
            return response.json()["embedding"]["values"]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        requests = [
            {"model": "models/text-embedding-004", "content": {"parts": [{"text": t}]}} for t in texts
        ]
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                _BATCH_EMBED_URL,
                params={"key": self._api_key},
                json={"requests": requests},
            )
            response.raise_for_status()
            return [e["values"] for e in response.json()["embeddings"]]
