"""
infrastructure/database/models/memory_model.py

Why this file exists:
    Postgres-facing shape of a memory row. Same separation-of-concerns
    rationale as every other *_model.py in this codebase.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class MemoryTypeEnum(str, enum.Enum):
    PREFERENCE = "preference"
    FACT = "fact"
    PROFILE = "profile"


class MemoryModel(Base):
    __tablename__ = "memories"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    memory_type: Mapped[MemoryTypeEnum] = mapped_column(Enum(MemoryTypeEnum), default=MemoryTypeEnum.FACT, nullable=False)
    importance_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    embedding_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    last_accessed_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)
