"""
application/use_cases/manage_memory.py

Why this file exists:
    Backs the "Memory controls" settings panel from the spec — lets a user
    see, add, and delete what VIRA remembers about them. Separate from the
    automatic memory extraction that (optionally) happens during chat.
"""

from uuid import UUID

from app.ai.memory.long_term import LongTermMemoryManager
from app.domain.entities.memory import Memory, MemoryType
from app.domain.exceptions.common_exceptions import AccessDeniedError
from app.domain.repositories.memory_repository import IMemoryRepository


class CreateMemoryUseCase:
    def __init__(self, long_term_memory: LongTermMemoryManager):
        self._long_term_memory = long_term_memory

    async def execute(self, user_id: UUID, content: str, memory_type: MemoryType, importance_score: float) -> Memory:
        return await self._long_term_memory.remember(user_id, content, memory_type, importance_score)


class ListMemoriesUseCase:
    def __init__(self, memory_repository: IMemoryRepository):
        self._memory_repository = memory_repository

    async def execute(self, user_id: UUID) -> list[Memory]:
        return await self._memory_repository.list_by_user(user_id)


class DeleteMemoryUseCase:
    def __init__(self, memory_repository: IMemoryRepository):
        self._memory_repository = memory_repository

    async def execute(self, user_id: UUID, memory_id: UUID) -> None:
        memory = await self._memory_repository.get_by_id(memory_id)
        if memory is None:
            return  # idempotent delete
        if memory.user_id != user_id:
            raise AccessDeniedError("memory")
        await self._memory_repository.delete(memory_id)
