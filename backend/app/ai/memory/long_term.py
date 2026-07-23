"""
ai/memory/long_term.py

Why this file exists:
    Manages durable, cross-conversation knowledge about a user: stores
    facts/preferences as embeddings for semantic retrieval, and ranks
    retrieval results by a blend of similarity, stated importance, and
    recency of use — not similarity alone. A memory that's highly similar
    but was stored once and never relevant since should rank below a
    slightly-less-similar memory that's proven consistently useful.

How it communicates with other modules:
    - Depends on IMemoryRepository (Postgres metadata), IVectorStore
      (embeddings), IEmbeddingProvider (interfaces, all injected)
    - Consumed by application/use_cases/send_message.py to inject relevant
      memories into the prompt, and by application/use_cases/manage_memory.py
      for direct CRUD
"""

import logging
import math
from datetime import datetime, timezone
from uuid import UUID

from app.ai.embeddings.base import IEmbeddingProvider
from app.domain.entities.memory import Memory, MemoryType
from app.domain.repositories.memory_repository import IMemoryRepository
from app.infrastructure.vector_store.base import IVectorStore, VectorRecord

logger = logging.getLogger(__name__)

_RECENCY_HALF_LIFE_DAYS = 14  # a memory's recency weight halves every 14 days since last use


def _namespace_for(user_id: UUID) -> str:
    return f"memories:{user_id}"


class LongTermMemoryManager:
    def __init__(
        self,
        memory_repository: IMemoryRepository,
        vector_store: IVectorStore,
        embedding_provider: IEmbeddingProvider,
    ):
        self._memory_repository = memory_repository
        self._vector_store = vector_store
        self._embedding_provider = embedding_provider

    async def remember(
        self, user_id: UUID, content: str, memory_type: MemoryType = MemoryType.FACT, importance_score: float = 0.5
    ) -> Memory:
        """Stores a new long-term memory: embeds the content, upserts the
        vector, and persists the metadata row."""
        vector = await self._embedding_provider.embed(content)
        memory = Memory(
            user_id=user_id, content=content, memory_type=memory_type, importance_score=importance_score
        )
        memory.embedding_id = str(memory.id)

        await self._vector_store.upsert(
            namespace=_namespace_for(user_id),
            records=[VectorRecord(id=memory.embedding_id, vector=vector, metadata={"user_id": str(user_id)})],
        )
        return await self._memory_repository.create(memory)

    async def recall(self, user_id: UUID, query: str, top_k: int = 5) -> list[Memory]:
        """Retrieves the most relevant memories for the given query,
        ranked by similarity * importance * recency decay."""
        query_vector = await self._embedding_provider.embed(query)
        # Over-fetch by similarity alone, then re-rank with importance/recency
        # so a lower-similarity-but-important memory still has a chance to
        # surface.
        candidates = await self._vector_store.search(
            namespace=_namespace_for(user_id), query_vector=query_vector, top_k=top_k * 4
        )
        if not candidates:
            return []

        memory_ids = [UUID(c.id) for c in candidates]
        memories = await self._memory_repository.get_by_ids(memory_ids)
        memories_by_id = {m.id: m for m in memories}
        similarity_by_id = {UUID(c.id): c.score for c in candidates}

        ranked = sorted(
            memories,
            key=lambda m: self._rank_score(m, similarity_by_id.get(m.id, 0.0)),
            reverse=True,
        )
        top = ranked[:top_k]

        for memory in top:
            await self._memory_repository.touch_last_accessed(memory.id)

        return top

    @staticmethod
    def _rank_score(memory: Memory, similarity: float) -> float:
        days_since_access = (datetime.now(timezone.utc) - memory.last_accessed_at).total_seconds() / 86400
        recency_weight = math.pow(0.5, days_since_access / _RECENCY_HALF_LIFE_DAYS)
        return similarity * 0.6 + memory.importance_score * 0.25 + recency_weight * 0.15
