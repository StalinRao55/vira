"""
api/v1/schemas/memory_schemas.py

Why this file exists:
    Wire format for the memory-controls settings panel: list what VIRA
    remembers, add a memory manually, delete one.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MemoryResponse(BaseModel):
    id: UUID
    content: str
    memory_type: str
    importance_score: float
    created_at: datetime
    last_accessed_at: datetime

    model_config = {"from_attributes": True}


class CreateMemoryRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    memory_type: str = "fact"
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)
