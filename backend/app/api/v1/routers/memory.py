"""
api/v1/routers/memory.py

Why this file exists:
    HTTP boundary for the "Memory controls" settings feature — lets users
    see and manage what VIRA has stored about them.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.dependencies import (
    get_create_memory_use_case,
    get_current_user,
    get_delete_memory_use_case,
    get_list_memories_use_case,
)
from app.api.v1.schemas.memory_schemas import CreateMemoryRequest, MemoryResponse
from app.application.use_cases.manage_memory import (
    CreateMemoryUseCase,
    DeleteMemoryUseCase,
    ListMemoriesUseCase,
)
from app.domain.entities.memory import MemoryType
from app.domain.entities.user import User
from app.domain.exceptions.common_exceptions import AccessDeniedError

router = APIRouter(prefix="/memories", tags=["memory"])


@router.get("", response_model=list[MemoryResponse])
async def list_memories(
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[ListMemoriesUseCase, Depends(get_list_memories_use_case)],
) -> list[MemoryResponse]:
    memories = await use_case.execute(user_id=current_user.id)
    return [MemoryResponse.model_validate(m) for m in memories]


@router.post("", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    body: CreateMemoryRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[CreateMemoryUseCase, Depends(get_create_memory_use_case)],
) -> MemoryResponse:
    memory = await use_case.execute(
        user_id=current_user.id,
        content=body.content,
        memory_type=MemoryType(body.memory_type),
        importance_score=body.importance_score,
    )
    return MemoryResponse.model_validate(memory)


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[DeleteMemoryUseCase, Depends(get_delete_memory_use_case)],
) -> None:
    try:
        await use_case.execute(user_id=current_user.id, memory_id=memory_id)
    except AccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
