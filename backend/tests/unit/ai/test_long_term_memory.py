"""
tests/unit/ai/test_long_term_memory.py

Why this file exists:
    Verifies the core promise of long-term memory: given several stored
    memories, recall() for a specific query returns the semantically
    relevant one first, not just whatever was stored most recently. Uses
    MockEmbeddingProvider + FaissVectorStore so this runs fully offline.
"""

from uuid import uuid4

import pytest

from app.ai.embeddings.mock_embedding_provider import MockEmbeddingProvider
from app.ai.memory.long_term import LongTermMemoryManager
from app.domain.entities.memory import Memory, MemoryType
from app.domain.repositories.memory_repository import IMemoryRepository
from app.infrastructure.vector_store.faiss_vector_store import FaissVectorStore


class InMemoryMemoryRepository(IMemoryRepository):
    def __init__(self):
        self._data: dict = {}

    async def get_by_id(self, memory_id):
        return self._data.get(memory_id)

    async def list_by_user(self, user_id, limit=100):
        return [m for m in self._data.values() if m.user_id == user_id][:limit]

    async def get_by_ids(self, memory_ids):
        return [self._data[mid] for mid in memory_ids if mid in self._data]

    async def create(self, memory: Memory):
        self._data[memory.id] = memory
        return memory

    async def touch_last_accessed(self, memory_id):
        pass

    async def delete(self, memory_id):
        self._data.pop(memory_id, None)


@pytest.mark.asyncio
async def test_recall_ranks_semantically_relevant_memory_first():
    manager = LongTermMemoryManager(
        memory_repository=InMemoryMemoryRepository(),
        vector_store=FaissVectorStore(dimensions=32),
        embedding_provider=MockEmbeddingProvider(),
    )
    user_id = uuid4()

    await manager.remember(user_id, "User prefers vegetarian food and avoids dairy", MemoryType.PREFERENCE)
    await manager.remember(user_id, "User's favorite programming language is Python", MemoryType.FACT)
    await manager.remember(user_id, "User lives in Berlin and works remotely", MemoryType.FACT)

    # MockEmbeddingProvider is a bag-of-words hash, not real semantics, so
    # the query is phrased with literal word overlap to the target memory.
    # A real embedding model (GeminiEmbeddingProvider) would rank this
    # correctly even without shared words.
    results = await manager.recall(user_id, query="food vegetarian dinner dairy", top_k=2)

    assert len(results) > 0
    assert "vegetarian" in results[0].content


@pytest.mark.asyncio
async def test_recall_scopes_to_the_requesting_user_only():
    manager = LongTermMemoryManager(
        memory_repository=InMemoryMemoryRepository(),
        vector_store=FaissVectorStore(dimensions=32),
        embedding_provider=MockEmbeddingProvider(),
    )
    user_a, user_b = uuid4(), uuid4()

    await manager.remember(user_a, "User A likes jazz music", MemoryType.PREFERENCE)
    await manager.remember(user_b, "User B likes jazz music", MemoryType.PREFERENCE)

    results = await manager.recall(user_a, query="jazz music", top_k=5)

    assert all(r.user_id == user_a for r in results)
