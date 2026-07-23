"""
infrastructure/database/repositories/postgres_document_repository.py

Why this file exists:
    Translates between domain Document/DocumentChunk entities and their
    ORM counterparts. Only place writing SQL/ORM for document data.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.document import Document, DocumentChunk, DocumentStatus
from app.domain.repositories.document_repository import IDocumentChunkRepository, IDocumentRepository
from app.infrastructure.database.models.document_models import (
    DocumentChunkModel,
    DocumentModel,
    DocumentStatusEnum,
)


def _document_to_entity(model: DocumentModel) -> Document:
    return Document(
        id=model.id,
        user_id=model.user_id,
        filename=model.filename,
        file_type=model.file_type,
        storage_path=model.storage_path,
        status=DocumentStatus(model.status.value),
        uploaded_at=model.uploaded_at,
    )


def _chunk_to_entity(model: DocumentChunkModel) -> DocumentChunk:
    return DocumentChunk(
        id=model.id,
        document_id=model.document_id,
        chunk_index=model.chunk_index,
        content=model.content,
        embedding_id=model.embedding_id,
        metadata=model.chunk_metadata,
    )


class PostgresDocumentRepository(IDocumentRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, document_id: UUID) -> Document | None:
        model = await self._session.get(DocumentModel, document_id)
        return _document_to_entity(model) if model else None

    async def list_by_user(self, user_id: UUID) -> list[Document]:
        stmt = select(DocumentModel).where(DocumentModel.user_id == user_id).order_by(DocumentModel.uploaded_at.desc())
        result = await self._session.execute(stmt)
        return [_document_to_entity(m) for m in result.scalars().all()]

    async def create(self, document: Document) -> Document:
        model = DocumentModel(
            id=document.id,
            user_id=document.user_id,
            filename=document.filename,
            file_type=document.file_type,
            storage_path=document.storage_path,
            status=DocumentStatusEnum(document.status.value),
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return _document_to_entity(model)

    async def update_status(self, document_id: UUID, status: DocumentStatus) -> None:
        model = await self._session.get(DocumentModel, document_id)
        if model is not None:
            model.status = DocumentStatusEnum(status.value)
            await self._session.commit()

    async def delete(self, document_id: UUID) -> None:
        model = await self._session.get(DocumentModel, document_id)
        if model is not None:
            await self._session.delete(model)
            await self._session.commit()


class PostgresDocumentChunkRepository(IDocumentChunkRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_many(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        models = [
            DocumentChunkModel(
                id=c.id,
                document_id=c.document_id,
                chunk_index=c.chunk_index,
                content=c.content,
                embedding_id=c.embedding_id,
                chunk_metadata=c.metadata,
            )
            for c in chunks
        ]
        self._session.add_all(models)
        await self._session.commit()
        return chunks

    async def list_by_document(self, document_id: UUID) -> list[DocumentChunk]:
        stmt = (
            select(DocumentChunkModel)
            .where(DocumentChunkModel.document_id == document_id)
            .order_by(DocumentChunkModel.chunk_index)
        )
        result = await self._session.execute(stmt)
        return [_chunk_to_entity(m) for m in result.scalars().all()]

    async def get_by_ids(self, chunk_ids: list[UUID]) -> list[DocumentChunk]:
        if not chunk_ids:
            return []
        stmt = select(DocumentChunkModel).where(DocumentChunkModel.id.in_(chunk_ids))
        result = await self._session.execute(stmt)
        return [_chunk_to_entity(m) for m in result.scalars().all()]

    async def delete_by_document(self, document_id: UUID) -> None:
        stmt = select(DocumentChunkModel).where(DocumentChunkModel.document_id == document_id)
        result = await self._session.execute(stmt)
        for model in result.scalars().all():
            await self._session.delete(model)
        await self._session.commit()
