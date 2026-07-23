"""
application/use_cases/list_conversations.py

Why this file exists:
    Backs the sidebar: paginated listing (infinite scroll) and title
    search, both scoped to the requesting user so one user can never see
    another's conversations.
"""

from uuid import UUID

from app.domain.entities.conversation import Conversation
from app.domain.repositories.chat_repository import IConversationRepository


class ListConversationsUseCase:
    def __init__(self, conversation_repository: IConversationRepository):
        self._conversation_repository = conversation_repository

    async def execute(
        self,
        user_id: UUID,
        include_archived: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Conversation]:
        return await self._conversation_repository.list_by_user(
            user_id=user_id, include_archived=include_archived, limit=limit, offset=offset
        )


class SearchConversationsUseCase:
    def __init__(self, conversation_repository: IConversationRepository):
        self._conversation_repository = conversation_repository

    async def execute(self, user_id: UUID, query: str) -> list[Conversation]:
        return await self._conversation_repository.search_by_title(user_id, query)
