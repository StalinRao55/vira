"""
api/v1/routers/conversations.py

Why this file exists:
    HTTP boundary for everything under "Conversation Architecture" in the
    spec except sending messages (that's messages.py, since it streams).
    Every handler stays thin: validate, call use case, catch domain
    exceptions, return schema.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.dependencies import (
    get_create_conversation_use_case,
    get_current_user,
    get_delete_conversation_use_case,
    get_list_conversations_use_case,
    get_search_conversations_use_case,
    get_update_conversation_use_case,
)
from app.api.v1.schemas.chat_schemas import ConversationResponse, ConversationUpdateRequest
from app.application.use_cases.create_conversation import CreateConversationUseCase
from app.application.use_cases.list_conversations import (
    ListConversationsUseCase,
    SearchConversationsUseCase,
)
from app.application.use_cases.update_conversation import (
    ConversationUpdate,
    DeleteConversationUseCase,
    UpdateConversationUseCase,
)
from app.domain.entities.user import User
from app.domain.exceptions.chat_exceptions import (
    ConversationAccessDeniedError,
    ConversationNotFoundError,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[CreateConversationUseCase, Depends(get_create_conversation_use_case)],
) -> ConversationResponse:
    conversation = await use_case.execute(user_id=current_user.id)
    return ConversationResponse.model_validate(conversation)


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[ListConversationsUseCase, Depends(get_list_conversations_use_case)],
    include_archived: bool = False,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
) -> list[ConversationResponse]:
    conversations = await use_case.execute(
        user_id=current_user.id, include_archived=include_archived, limit=limit, offset=offset
    )
    return [ConversationResponse.model_validate(c) for c in conversations]


@router.get("/search", response_model=list[ConversationResponse])
async def search_conversations(
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[SearchConversationsUseCase, Depends(get_search_conversations_use_case)],
    q: str = Query(min_length=1),
) -> list[ConversationResponse]:
    conversations = await use_case.execute(user_id=current_user.id, query=q)
    return [ConversationResponse.model_validate(c) for c in conversations]


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    body: ConversationUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[UpdateConversationUseCase, Depends(get_update_conversation_use_case)],
) -> ConversationResponse:
    try:
        conversation = await use_case.execute(
            user_id=current_user.id,
            conversation_id=conversation_id,
            update=ConversationUpdate(**body.model_dump(exclude_unset=True)),
        )
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConversationAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return ConversationResponse.model_validate(conversation)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[DeleteConversationUseCase, Depends(get_delete_conversation_use_case)],
) -> None:
    try:
        await use_case.execute(user_id=current_user.id, conversation_id=conversation_id)
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConversationAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
