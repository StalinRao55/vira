"""
domain/repositories/document_repository.py

Why this file exists:
    Contracts for persisting document metadata and chunks in Postgres,
    kept separate from the vector store (which holds only the embeddings,
    same split as Memory in Phase 6).
"""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.document import Document, DocumentChunk, DocumentStatus


class IDocumentRepository(ABC):
    @abstractmethod
    async def get_by_id(self, document_id: UUID) -> Document | None: ...

    @abstractmethod
    async def list_by_user(self, user_id: UUID) -> list[Document]: ...

    @abstractmethod
    async def create(self, document: Document) -> Document: ...

    @abstractmethod
    async def update_status(self, document_id: UUID, status: DocumentStatus) -> None: ...

    @abstractmethod
    async def delete(self, document_id: UUID) -> None: ...


class IDocumentChunkRepository(ABC):
    @abstractmethod
    async def create_many(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]: ...

    @abstractmethod
    async def list_by_document(self, document_id: UUID) -> list[DocumentChunk]: ...

    @abstractmethod
    async def get_by_ids(self, chunk_ids: list[UUID]) -> list[DocumentChunk]: ...

    @abstractmethod
    async def delete_by_document(self, document_id: UUID) -> None: ...
