"""
application/use_cases/search_documents.py

Why this file exists:
    Backs both the standalone "search my documents" endpoint and the
    document-context injection inside SendMessageUseCase. RAGEngine.retrieve
    only returns scores + document/chunk-index metadata (the vector store
    never holds text) — this use case fills in the actual chunk content
    from Postgres before handing results back.
"""

from uuid import UUID

from app.ai.rag.rag_engine import RAGEngine, RetrievedChunk
from app.domain.repositories.document_repository import IDocumentChunkRepository, IDocumentRepository


class SearchDocumentsUseCase:
    def __init__(
        self,
        rag_engine: RAGEngine,
        document_repository: IDocumentRepository,
        chunk_repository: IDocumentChunkRepository,
    ):
        self._rag_engine = rag_engine
        self._document_repository = document_repository
        self._chunk_repository = chunk_repository

    async def execute(self, user_id: UUID, query: str, document_ids: list[UUID], top_k: int = 5) -> list[RetrievedChunk]:
        # Ownership check: only search documents that belong to this user,
        # regardless of which document_ids were requested.
        owned_documents = {d.id: d for d in await self._document_repository.list_by_user(user_id)}
        scoped_ids = [did for did in document_ids if did in owned_documents]
        if not scoped_ids:
            return []

        filenames_by_id = {did: owned_documents[did].filename for did in scoped_ids}
        results = await self._rag_engine.retrieve(query, scoped_ids, filenames_by_id, top_k)

        # Fill in actual chunk text (vector store holds only vectors + light
        # metadata, never the content itself).
        for document_id in scoped_ids:
            chunks = await self._chunk_repository.list_by_document(document_id)
            content_by_index = {c.chunk_index: c.content for c in chunks}
            for result in results:
                if result.document_id == document_id:
                    result.content = content_by_index.get(result.chunk_index, "")

        return [r for r in results if r.content]
