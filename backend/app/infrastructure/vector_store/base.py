"""
infrastructure/vector_store/base.py

Why this file exists:
    Defines the contract for storing/searching embeddings, independent of
    FAISS vs Qdrant vs Pinecone. Both the long-term memory manager (this
    phase) and the RAG engine (Phase 7) depend on this interface only.
    This is the seam the spec calls out explicitly: "Support Pinecone/Qdrant
    for production" without changing business logic.

How it communicates with other modules:
    - Implemented by faiss_vector_store.py (dev), and a future
      qdrant_vector_store.py (prod)
    - Consumed by ai/memory/long_term.py, and Phase 7's RAG retriever
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class VectorRecord:
    """One entry in the vector store. `id` links back to the owning
    Postgres row (a Memory or DocumentChunk) — the vector store never
    holds business data itself, only vectors + a thin metadata dict for
    filtering (e.g. user_id, namespace)."""

    id: str
    vector: list[float]
    metadata: dict


@dataclass
class VectorSearchResult:
    id: str
    score: float
    metadata: dict


class IVectorStore(ABC):
    @abstractmethod
    async def upsert(self, namespace: str, records: list[VectorRecord]) -> None: ...

    @abstractmethod
    async def search(
        self,
        namespace: str,
        query_vector: list[float],
        top_k: int = 5,
        metadata_filter: dict | None = None,
    ) -> list[VectorSearchResult]: ...

    @abstractmethod
    async def delete(self, namespace: str, ids: list[str]) -> None: ...
