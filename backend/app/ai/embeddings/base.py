"""
ai/embeddings/base.py

Why this file exists:
    Text embedding is a separate concern from text generation (different
    endpoint, different model, often a different provider entirely), so it
    gets its own interface rather than being bolted onto ILLMProvider. Both
    the memory system and the RAG engine (Phase 7) depend on this
    interface, never on a concrete embedding provider.

How it communicates with other modules:
    - Implemented by gemini_embedding_provider.py, mock_embedding_provider.py
    - Consumed by ai/memory/long_term.py and (Phase 7) ai/rag/*
"""

from abc import ABC, abstractmethod


class IEmbeddingProvider(ABC):
    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Vector dimensionality this provider produces — vector stores
        need this to size their index."""
        ...

    @abstractmethod
    async def embed(self, text: str) -> list[float]: ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Batched embedding — implementations should call the provider's
        batch endpoint where available rather than looping embed()."""
        ...
