"""
application/use_cases/update_conversation.py

Why this file exists:
    Rename / pin / favorite / archive all follow the identical pattern:
    load conversation, verify ownership, mutate one field, save. Rather
    than four near-duplicate use case classes, this exposes one execute()
    that takes a partial-update dict — the ownership check lives in exactly
    one place.

How it communicates with other modules:
    - Depends on IConversationRepository
    - Raises ConversationNotFoundError / ConversationAccessDeniedError,
      caught by api/v1/routers/conversations.py
"""

from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.conversation import Conversation
from app.domain.exceptions.chat_exceptions import (
    ConversationAccessDeniedError,
    ConversationNotFoundError,
)
from app.domain.repositories.chat_repository import IConversationRepository


@dataclass
class ConversationUpdate:
    title: str | None = None
    is_archived: bool | None = None
    is_pinned: bool | None = None
    is_favorite: bool | None = None


class UpdateConversationUseCase:
    def __init__(self, conversation_repository: IConversationRepository):
        self._conversation_repository = conversation_repository

    async def execute(self, user_id: UUID, conversation_id: UUID, update: ConversationUpdate) -> Conversation:
        conversation = await self._conversation_repository.get_by_id(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError(conversation_id)
        if conversation.user_id != user_id:
            raise ConversationAccessDeniedError()

        if update.title is not None:
            conversation.title = update.title
        if update.is_archived is not None:
            conversation.is_archived = update.is_archived
        if update.is_pinned is not None:
            conversation.is_pinned = update.is_pinned
        if update.is_favorite is not None:
            conversation.is_favorite = update.is_favorite

        return await self._conversation_repository.update(conversation)


class DeleteConversationUseCase:
    def __init__(self, conversation_repository: IConversationRepository):
        self._conversation_repository = conversation_repository

    async def execute(self, user_id: UUID, conversation_id: UUID) -> None:
        conversation = await self._conversation_repository.get_by_id(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError(conversation_id)
        if conversation.user_id != user_id:
            raise ConversationAccessDeniedError()
        await self._conversation_repository.delete(conversation_id)
