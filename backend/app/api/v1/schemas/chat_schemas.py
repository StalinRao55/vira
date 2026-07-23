"""
api/v1/schemas/chat_schemas.py

Why this file exists:
    Wire format for conversation/message endpoints, separate from domain
    entities for the same reasons as auth_schemas.py in Phase 4.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ConversationResponse(BaseModel):
    id: UUID
    title: str
    is_archived: bool
    is_pinned: bool
    is_favorite: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    is_archived: bool | None = None
    is_pinned: bool | None = None
    is_favorite: bool | None = None


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    model_provider: str | None
    model_name: str | None
    token_count: int | None
    is_edited: bool
    parent_message_id: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=32_000)
    model: str = "gemini-3-flash"
    document_ids: list[UUID] = Field(default_factory=list)
