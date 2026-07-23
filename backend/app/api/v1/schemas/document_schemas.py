"""
api/v1/schemas/document_schemas.py

Why this file exists:
    Wire format for document upload/list/search — separate from the
    domain Document/DocumentChunk entities per the established pattern.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    id: UUID
    filename: str
    file_type: str
    status: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class DocumentSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    document_ids: list[UUID]
    top_k: int = Field(default=5, ge=1, le=20)


class RetrievedChunkResponse(BaseModel):
    content: str
    score: float
    document_id: UUID
    document_filename: str
    chunk_index: int
    page: int | None = None
