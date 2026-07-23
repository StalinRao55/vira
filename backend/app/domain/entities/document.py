"""
domain/entities/document.py

Why this file exists:
    Business definitions for uploaded documents and their retrieval-sized
    chunks. `Document.status` tracks the async ingestion pipeline (a large
    PDF can take a few seconds to extract/chunk/embed) so the UI can show
    "processing" rather than pretending it's instantly searchable.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class DocumentStatus(str, Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


@dataclass
class Document:
    user_id: UUID
    filename: str
    file_type: str
    storage_path: str
    status: DocumentStatus = DocumentStatus.PROCESSING
    id: UUID = field(default_factory=uuid4)
    uploaded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class DocumentChunk:
    document_id: UUID
    chunk_index: int
    content: str
    embedding_id: str | None = None
    metadata: dict = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
