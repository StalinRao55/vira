"""
domain/entities/message.py

Why this file exists:
    Business definition of a single message. `parent_message_id` is the
    mechanism behind "regenerate response" and "edit message": a
    regenerated assistant reply is a NEW message row pointing at the same
    parent user message, rather than mutating history in place.

How it communicates with other modules:
    - infrastructure/database/repositories/postgres_message_repository
      converts between this and the ORM MessageModel
    - application/use_cases/send_message.py creates and persists these
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass
class Message:
    conversation_id: UUID
    role: MessageRole
    content: str
    model_provider: str | None = None
    model_name: str | None = None
    token_count: int | None = None
    is_edited: bool = False
    parent_message_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
