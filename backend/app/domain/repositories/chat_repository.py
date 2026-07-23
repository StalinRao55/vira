"""
domain/repositories/chat_repository.py

Why this file exists:
    Contracts for persisting conversations and messages, kept separate from
    any SQL/ORM concern. application/use_cases/* depend on these
    interfaces only, so they're testable with in-memory fakes (see
    tests/unit/application/test_send_message.py).

How it communicates with other modules:
    - Implemented by infrastructure/database/repositories/
      postgres_conversation_repository.py and postgres_message_repository.py
"""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.conversation import Conversation
from app.domain.entities.message import Message


class IConversationRepository(ABC):
    @abstractmethod
    async def get_by_id(self, conversation_id: UUID) -> Conversation | None: ...

    @abstractmethod
    async def list_by_user(
        self,
        user_id: UUID,
        include_archived: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Conversation]: ...

    @abstractmethod
    async def search_by_title(self, user_id: UUID, query: str) -> list[Conversation]: ...

    @abstractmethod
    async def create(self, conversation: Conversation) -> Conversation: ...

    @abstractmethod
    async def update(self, conversation: Conversation) -> Conversation: ...

    @abstractmethod
    async def delete(self, conversation_id: UUID) -> None: ...


class IMessageRepository(ABC):
    @abstractmethod
    async def get_by_id(self, message_id: UUID) -> Message | None: ...

    @abstractmethod
    async def list_by_conversation(
        self,
        conversation_id: UUID,
        limit: int = 50,
        before: UUID | None = None,
    ) -> list[Message]:
        """`before` enables cursor-based infinite scroll (from the spec) —
        pass the oldest loaded message id to fetch the next page further
        back in history."""
        ...

    @abstractmethod
    async def create(self, message: Message) -> Message: ...
