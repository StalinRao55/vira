"""
application/use_cases/create_conversation.py

Why this file exists:
    Encapsulates conversation creation. Trivial today, but this is the
    natural extension point if creation later needs side effects (e.g.
    initializing a default folder, emitting an analytics event).
"""

from uuid import UUID

from app.domain.entities.conversation import Conversation
from app.domain.repositories.chat_repository import IConversationRepository


class CreateConversationUseCase:
    def __init__(self, conversation_repository: IConversationRepository):
        self._conversation_repository = conversation_repository

    async def execute(self, user_id: UUID) -> Conversation:
        conversation = Conversation(user_id=user_id)
        return await self._conversation_repository.create(conversation)
