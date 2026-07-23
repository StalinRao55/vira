"""
application/use_cases/manage_documents.py

Why this file exists:
    Backs the document management side of the RAG UI: listing a user's
    uploads and deleting one (which must clean up Postgres rows, vector
    store entries, AND the stored file — three systems to keep in sync).
"""

import logging
from uuid import UUID

from app.domain.entities.document import Document
from app.domain.exceptions.common_exceptions import AccessDeniedError
from app.domain.exceptions.document_exceptions import DocumentNotFoundError
from app.domain.repositories.document_repository import IDocumentChunkRepository, IDocumentRepository
from app.infrastructure.storage.base import IFileStorage
from app.infrastructure.vector_store.base import IVectorStore

logger = logging.getLogger(__name__)


class ListDocumentsUseCase:
    def __init__(self, document_repository: IDocumentRepository):
        self._document_repository = document_repository

    async def execute(self, user_id: UUID) -> list[Document]:
        return await self._document_repository.list_by_user(user_id)


class DeleteDocumentUseCase:
    def __init__(
        self,
        document_repository: IDocumentRepository,
        chunk_repository: IDocumentChunkRepository,
        file_storage: IFileStorage,
        vector_store: IVectorStore,
    ):
        self._document_repository = document_repository
        self._chunk_repository = chunk_repository
        self._file_storage = file_storage
        self._vector_store = vector_store

    async def execute(self, user_id: UUID, document_id: UUID) -> None:
        document = await self._document_repository.get_by_id(document_id)
        if document is None:
            raise DocumentNotFoundError(document_id)
        if document.user_id != user_id:
            raise AccessDeniedError("document")

        chunks = await self._chunk_repository.list_by_document(document_id)
        embedding_ids = [c.embedding_id for c in chunks if c.embedding_id]
        if embedding_ids:
            await self._vector_store.delete(namespace=f"documents:{document_id}", ids=embedding_ids)

        await self._chunk_repository.delete_by_document(document_id)
        await self._file_storage.delete(document.storage_path)
        await self._document_repository.delete(document_id)
        logger.info("Deleted document %s and %d chunks", document_id, len(chunks))
