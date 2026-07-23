"""
domain/entities/conversation.py

Why this file exists:
    Business definition of a conversation — a thread of messages owned by a
    user, with the organizational metadata (pin/favorite/archive) called
    for in the spec. No framework or ORM dependency.

How it communicates with other modules:
    - infrastructure/database/repositories/postgres_conversation_repository
      converts between this and the ORM ConversationModel
    - application/use_cases/* operate on this entity
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass
class Conversation:
    user_id: UUID
    title: str = "New conversation"
    is_archived: bool = False
    is_pinned: bool = False
    is_favorite: bool = False
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def needs_title_generation(self) -> bool:
        """A conversation still has its placeholder title until the first
        exchange completes — used by SendMessageUseCase to decide whether
        to trigger auto-titling."""
        return self.title == "New conversation"
