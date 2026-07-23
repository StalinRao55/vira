"""
ai/embeddings/mock_embedding_provider.py

Why this file exists:
    Lets us test memory ranking and retrieval logic offline and
    deterministically. Uses a simple hashing scheme so that similar text
    produces similar (but not identical, unless truly equal) vectors —
    good enough to verify "most similar comes back first" without a real
    model.

How it communicates with other modules:
    - Implements ai/embeddings/base.IEmbeddingProvider
    - Used directly in tests/unit/ai/test_long_term_memory.py
"""

import hashlib

from app.ai.embeddings.base import IEmbeddingProvider

_DIM = 32


class MockEmbeddingProvider(IEmbeddingProvider):
    @property
    def dimensions(self) -> int:
        return _DIM

    async def embed(self, text: str) -> list[float]:
        # Bag-of-words hashing: each word contributes to a fixed-size
        # vector via its hash, so texts sharing words end up with
        # noticeably higher cosine similarity than unrelated texts.
        vector = [0.0] * _DIM
        for word in text.lower().split():
            digest = hashlib.md5(word.encode()).digest()
            index = digest[0] % _DIM
            vector[index] += 1.0
        norm = sum(v * v for v in vector) ** 0.5
        return [v / norm for v in vector] if norm > 0 else vector

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed(t) for t in texts]
