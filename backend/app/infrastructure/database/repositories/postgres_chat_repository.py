"""
infrastructure/database/repositories/postgres_chat_repository.py

Why this file exists:
    Translates between domain entities (Conversation, Message) and their
    ORM counterparts. The only place in the codebase that writes SQL/ORM
    queries for chat data.

How it communicates with other modules:
    - Implements domain/repositories/chat_repository.IConversationRepository
      and IMessageRepository
    - Injected into use cases via api/v1/dependencies.py
"""

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.conversation import Conversation
from app.domain.entities.message import Message, MessageRole
from app.domain.repositories.chat_repository import IConversationRepository, IMessageRepository
from app.infrastructure.database.models.chat_models import ConversationModel, MessageModel, MessageRoleEnum


def _conversation_to_entity(model: ConversationModel) -> Conversation:
    return Conversation(
        id=model.id,
        user_id=model.user_id,
        title=model.title,
        is_archived=model.is_archived,
        is_pinned=model.is_pinned,
        is_favorite=model.is_favorite,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _message_to_entity(model: MessageModel) -> Message:
    return Message(
        id=model.id,
        conversation_id=model.conversation_id,
        role=MessageRole(model.role.value),
        content=model.content,
        model_provider=model.model_provider,
        model_name=model.model_name,
        token_count=model.token_count,
        is_edited=model.is_edited,
        parent_message_id=model.parent_message_id,
        created_at=model.created_at,
    )


class PostgresConversationRepository(IConversationRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, conversation_id: UUID) -> Conversation | None:
        model = await self._session.get(ConversationModel, conversation_id)
        return _conversation_to_entity(model) if model else None

    async def list_by_user(
        self, user_id: UUID, include_archived: bool = False, limit: int = 50, offset: int = 0
    ) -> list[Conversation]:
        stmt = select(ConversationModel).where(ConversationModel.user_id == user_id)
        if not include_archived:
            stmt = stmt.where(ConversationModel.is_archived.is_(False))
        stmt = (
            stmt.order_by(ConversationModel.is_pinned.desc(), ConversationModel.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [_conversation_to_entity(m) for m in result.scalars().all()]

    async def search_by_title(self, user_id: UUID, query: str) -> list[Conversation]:
        stmt = select(ConversationModel).where(
            ConversationModel.user_id == user_id,
            ConversationModel.title.ilike(f"%{query}%"),
        )
        result = await self._session.execute(stmt)
        return [_conversation_to_entity(m) for m in result.scalars().all()]

    async def create(self, conversation: Conversation) -> Conversation:
        model = ConversationModel(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            is_archived=conversation.is_archived,
            is_pinned=conversation.is_pinned,
            is_favorite=conversation.is_favorite,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return _conversation_to_entity(model)

    async def update(self, conversation: Conversation) -> Conversation:
        model = await self._session.get(ConversationModel, conversation.id)
        if model is None:
            raise ValueError(f"Conversation {conversation.id} not found for update")
        model.title = conversation.title
        model.is_archived = conversation.is_archived
        model.is_pinned = conversation.is_pinned
        model.is_favorite = conversation.is_favorite
        await self._session.commit()
        await self._session.refresh(model)
        return _conversation_to_entity(model)

    async def delete(self, conversation_id: UUID) -> None:
        model = await self._session.get(ConversationModel, conversation_id)
        if model is not None:
            await self._session.delete(model)
            await self._session.commit()


class PostgresMessageRepository(IMessageRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, message_id: UUID) -> Message | None:
        model = await self._session.get(MessageModel, message_id)
        return _message_to_entity(model) if model else None

    async def list_by_conversation(
        self, conversation_id: UUID, limit: int = 50, before: UUID | None = None
    ) -> list[Message]:
        stmt = select(MessageModel).where(MessageModel.conversation_id == conversation_id)
        if before is not None:
            # Cursor-based pagination for infinite scroll: fetch messages
            # older than the given message's timestamp.
            cursor_model = await self._session.get(MessageModel, before)
            if cursor_model is not None:
                stmt = stmt.where(MessageModel.created_at < cursor_model.created_at)
        stmt = stmt.order_by(MessageModel.created_at.asc()).limit(limit)
        result = await self._session.execute(stmt)
        return [_message_to_entity(m) for m in result.scalars().all()]

    async def create(self, message: Message) -> Message:
        model = MessageModel(
            id=message.id,
            conversation_id=message.conversation_id,
            role=MessageRoleEnum(message.role.value),
            content=message.content,
            model_provider=message.model_provider,
            model_name=message.model_name,
            token_count=message.token_count,
            is_edited=message.is_edited,
            parent_message_id=message.parent_message_id,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return _message_to_entity(model)
