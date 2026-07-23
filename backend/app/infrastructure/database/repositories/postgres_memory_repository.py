"""
infrastructure/database/repositories/postgres_memory_repository.py

Why this file exists:
    Translates between the domain Memory entity and MemoryModel. Only
    place in the codebase writing SQL/ORM queries for memory metadata.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.memory import Memory, MemoryType
from app.domain.repositories.memory_repository import IMemoryRepository
from app.infrastructure.database.models.memory_model import MemoryModel, MemoryTypeEnum


def _to_entity(model: MemoryModel) -> Memory:
    return Memory(
        id=model.id,
        user_id=model.user_id,
        content=model.content,
        memory_type=MemoryType(model.memory_type.value),
        importance_score=model.importance_score,
        embedding_id=model.embedding_id,
        created_at=model.created_at,
        last_accessed_at=model.last_accessed_at,
    )


class PostgresMemoryRepository(IMemoryRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, memory_id: UUID) -> Memory | None:
        model = await self._session.get(MemoryModel, memory_id)
        return _to_entity(model) if model else None

    async def list_by_user(self, user_id: UUID, limit: int = 100) -> list[Memory]:
        stmt = (
            select(MemoryModel)
            .where(MemoryModel.user_id == user_id)
            .order_by(MemoryModel.last_accessed_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [_to_entity(m) for m in result.scalars().all()]

    async def get_by_ids(self, memory_ids: list[UUID]) -> list[Memory]:
        if not memory_ids:
            return []
        stmt = select(MemoryModel).where(MemoryModel.id.in_(memory_ids))
        result = await self._session.execute(stmt)
        return [_to_entity(m) for m in result.scalars().all()]

    async def create(self, memory: Memory) -> Memory:
        model = MemoryModel(
            id=memory.id,
            user_id=memory.user_id,
            content=memory.content,
            memory_type=MemoryTypeEnum(memory.memory_type.value),
            importance_score=memory.importance_score,
            embedding_id=memory.embedding_id,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return _to_entity(model)

    async def touch_last_accessed(self, memory_id: UUID) -> None:
        model = await self._session.get(MemoryModel, memory_id)
        if model is not None:
            model.last_accessed_at = datetime.now(timezone.utc)
            await self._session.commit()

    async def delete(self, memory_id: UUID) -> None:
        model = await self._session.get(MemoryModel, memory_id)
        if model is not None:
            await self._session.delete(model)
            await self._session.commit()
