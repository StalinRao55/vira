"""
tests/unit/ai/test_rag_engine.py

Why this file exists:
    Verifies the full ingest -> retrieve loop works and that retrieval
    results carry correct citation metadata (document filename, chunk
    index) — the part of RAG that's easy to get functionally working but
    silently wrong on citations.
"""

from uuid import uuid4

import pytest

from app.ai.embeddings.mock_embedding_provider import MockEmbeddingProvider
from app.ai.rag.rag_engine import RAGEngine
from app.infrastructure.vector_store.faiss_vector_store import FaissVectorStore


@pytest.mark.asyncio
async def test_ingest_and_retrieve_with_citations():
    engine = RAGEngine(embedding_provider=MockEmbeddingProvider(), vector_store=FaissVectorStore(dimensions=32))
    document_id = uuid4()

    text = (
        b"The quarterly revenue grew by twelve percent this year.\n\n"
        b"Employee headcount increased to five hundred people.\n\n"
        b"The new office is located in downtown Berlin near the river."
    )
    chunks = await engine.ingest(document_id, text, "txt")

    assert len(chunks) >= 1
    assert all(c.embedding_id is not None for c in chunks)

    results = await engine.retrieve(
        query="revenue growth percent",
        document_ids=[document_id],
        filenames_by_id={document_id: "quarterly_report.txt"},
        top_k=3,
    )

    assert len(results) > 0
    assert all(r.document_filename == "quarterly_report.txt" for r in results)
    assert all(r.document_id == document_id for r in results)
    # chunk_index should be a real index from ingestion, not the -1 default
    assert all(r.chunk_index >= 0 for r in results)


@pytest.mark.asyncio
async def test_retrieve_with_no_document_ids_returns_empty():
    engine = RAGEngine(embedding_provider=MockEmbeddingProvider(), vector_store=FaissVectorStore(dimensions=32))
    results = await engine.retrieve(query="anything", document_ids=[], filenames_by_id={})
    assert results == []
