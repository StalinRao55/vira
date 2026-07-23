"""
domain/entities/memory.py

Why this file exists:
    Business definition of a long-term memory: a fact/preference about a
    user, with an importance score used for ranking and a link to its
    vector-store entry.

How it communicates with other modules:
    - infrastructure/database/repositories/postgres_memory_repository.py
      converts between this and the ORM model
    - ai/memory/long_term.py operates on this entity
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class MemoryType(str, Enum):
    PREFERENCE = "preference"
    FACT = "fact"
    PROFILE = "profile"


@dataclass
class Memory:
    user_id: UUID
    content: str
    memory_type: MemoryType = MemoryType.FACT
    importance_score: float = 0.5
    embedding_id: str | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
