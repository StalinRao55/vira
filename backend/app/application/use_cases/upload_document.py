"""
application/use_cases/upload_document.py

Why this file exists:
    Orchestrates the full ingestion pipeline: save the raw file, create the
    Document row, run it through RAGEngine (extract/chunk/embed/store),
    persist the resulting chunks, and flip status to ready or failed. This
    is intentionally synchronous within the request for now — Phase 13's
    notes cover moving this to a background task queue for large files so
    upload requests don't block on embedding API calls.
"""

import logging
from uuid import UUID

from app.ai.rag.rag_engine import RAGEngine
from app.domain.entities.document import Document, DocumentStatus
from app.domain.exceptions.document_exceptions import DocumentProcessingError
from app.domain.repositories.document_repository import IDocumentChunkRepository, IDocumentRepository
from app.infrastructure.storage.base import IFileStorage

logger = logging.getLogger(__name__)

_SUPPORTED_TYPES = {"pdf", "docx", "txt", "md", "markdown"}


class UploadDocumentUseCase:
    def __init__(
        self,
        document_repository: IDocumentRepository,
        chunk_repository: IDocumentChunkRepository,
        file_storage: IFileStorage,
        rag_engine: RAGEngine,
    ):
        self._document_repository = document_repository
        self._chunk_repository = chunk_repository
        self._file_storage = file_storage
        self._rag_engine = rag_engine

    async def execute(self, user_id: UUID, filename: str, content: bytes) -> Document:
        file_type = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if file_type not in _SUPPORTED_TYPES:
            raise DocumentProcessingError(f"Unsupported file type '.{file_type}'. Supported: {_SUPPORTED_TYPES}")

        document = Document(user_id=user_id, filename=filename, file_type=file_type, storage_path="")
        storage_path = await self._file_storage.save(f"{user_id}/{document.id}_{filename}", content)
        document.storage_path = storage_path
        document = await self._document_repository.create(document)

        try:
            chunks = await self._rag_engine.ingest(document.id, content, file_type)
            if chunks:
                await self._chunk_repository.create_many(chunks)
            await self._document_repository.update_status(document.id, DocumentStatus.READY)
            document.status = DocumentStatus.READY
            logger.info("Document %s ingested successfully: %d chunks", document.id, len(chunks))
        except Exception:
            logger.exception("Document ingestion failed for %s", document.id)
            await self._document_repository.update_status(document.id, DocumentStatus.FAILED)
            document.status = DocumentStatus.FAILED

        return document
