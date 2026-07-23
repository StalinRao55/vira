"""
ai/rag/rag_engine.py

Why this file exists:
    The RAG pipeline's orchestration point, matching the spec's flow:
    Upload -> Extraction -> Cleaning -> Chunking -> Embeddings -> Vector DB
    -> Semantic Search -> Context Injection -> LLM. Extraction lives in
    text_extractor.py and chunking in chunker.py; this class ties them to
    the embedding provider and vector store and adds the piece that makes
    retrieval useful rather than just "some text back": citation metadata
    on every result, and multi-document search.

How it communicates with other modules:
    - Depends on ai/embeddings/base.IEmbeddingProvider,
      infrastructure/vector_store/base.IVectorStore (interfaces, injected)
    - Uses ai/rag/text_extractor and ai/rag/chunker
    - Consumed by application/use_cases/upload_document.py (ingestion) and
      application/use_cases/search_documents.py (retrieval)
"""

import logging
from dataclasses import dataclass
from uuid import UUID

from app.ai.embeddings.base import IEmbeddingProvider
from app.ai.rag.chunker import chunk_text
from app.ai.rag.text_extractor import extract_text
from app.domain.entities.document import DocumentChunk
from app.infrastructure.vector_store.base import IVectorStore, VectorRecord

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    """A retrieval result carrying everything needed to cite its source —
    this is what makes RAG answers verifiable rather than just plausible."""

    content: str
    score: float
    document_id: UUID
    document_filename: str
    chunk_index: int
    page: int | None = None


def _namespace_for(document_id: UUID) -> str:
    return f"documents:{document_id}"


class RAGEngine:
    def __init__(self, embedding_provider: IEmbeddingProvider, vector_store: IVectorStore):
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store

    async def ingest(self, document_id: UUID, file_content: bytes, file_type: str) -> list[DocumentChunk]:
        """Extraction -> chunking -> embedding -> vector storage. Returns
        the DocumentChunk entities (without vectors, which stay in the
        vector store) for the caller to persist in Postgres."""
        raw_text = extract_text(file_content, file_type)
        pieces = chunk_text(raw_text)

        if not pieces:
            logger.warning("Document %s produced no extractable text", document_id)
            return []

        embeddings = await self._embedding_provider.embed_batch([p.content for p in pieces])

        document_chunks = []
        vector_records = []
        for piece, vector in zip(pieces, embeddings):
            chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=piece.chunk_index,
                content=piece.content,
                metadata=piece.metadata,
            )
            chunk.embedding_id = str(chunk.id)
            document_chunks.append(chunk)
            vector_records.append(
                VectorRecord(
                    id=chunk.embedding_id,
                    vector=vector,
                    metadata={"document_id": str(document_id), "chunk_index": chunk.chunk_index},
                )
            )

        await self._vector_store.upsert(namespace=_namespace_for(document_id), records=vector_records)
        logger.info("Ingested document %s into %d chunks", document_id, len(document_chunks))
        return document_chunks

    async def retrieve(
        self,
        query: str,
        document_ids: list[UUID],
        filenames_by_id: dict[UUID, str],
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        """Multi-document semantic search: queries each document's
        namespace and merges results by score. Each result carries its
        source filename and chunk index for citation display."""
        if not document_ids:
            return []

        query_vector = await self._embedding_provider.embed(query)

        all_results: list[RetrievedChunk] = []
        for document_id in document_ids:
            hits = await self._vector_store.search(
                namespace=_namespace_for(document_id), query_vector=query_vector, top_k=top_k
            )
            for hit in hits:
                all_results.append(
                    RetrievedChunk(
                        content="",  # filled in by the use case from Postgres (vector store holds no text)
                        score=hit.score,
                        document_id=document_id,
                        document_filename=filenames_by_id.get(document_id, "unknown"),
                        chunk_index=hit.metadata.get("chunk_index", -1),
                    )
                )

        all_results.sort(key=lambda r: r.score, reverse=True)
        return all_results[:top_k]
