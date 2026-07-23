"""
domain/repositories/memory_repository.py

Why this file exists:
    Contract for persisting memory METADATA (content, type, importance) in
    Postgres. The actual embedding vector lives in the vector store — see
    infrastructure/vector_store/base.py — this repository only stores the
    relational side and the embedding_id that links the two.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.memory import Memory


class IMemoryRepository(ABC):
    @abstractmethod
    async def get_by_id(self, memory_id: UUID) -> Memory | None: ...

    @abstractmethod
    async def list_by_user(self, user_id: UUID, limit: int = 100) -> list[Memory]: ...

    @abstractmethod
    async def get_by_ids(self, memory_ids: list[UUID]) -> list[Memory]: ...

    @abstractmethod
    async def create(self, memory: Memory) -> Memory: ...

    @abstractmethod
    async def touch_last_accessed(self, memory_id: UUID) -> None:
        """Updates last_accessed_at — called whenever a memory is retrieved
        for relevance ranking, so frequently-useful memories rank higher
        over time."""
        ...

    @abstractmethod
    async def delete(self, memory_id: UUID) -> None: ...
