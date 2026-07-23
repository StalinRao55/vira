"""
infrastructure/vector_store/faiss_vector_store.py

Why this file exists:
    Dev-time IVectorStore implementation using FAISS, an in-process vector
    index with zero external services to run. One FAISS index per
    namespace (e.g. "memories:{user_id}" or "documents:{document_id}"),
    kept in memory with an id-to-metadata sidecar dict since FAISS itself
    only stores vectors.

    IMPORTANT CAVEAT (documented, not hidden): this in-memory implementation
    does not persist across process restarts. That's fine for local dev
    iteration; Phase 13 notes the swap to QdrantVectorStore for anything
    that needs durability, including staging/production.

How it communicates with other modules:
    - Implements infrastructure/vector_store/base.IVectorStore
    - Instantiated by infrastructure/vector_store/factory.py
"""

import numpy as np

from app.infrastructure.vector_store.base import IVectorStore, VectorRecord, VectorSearchResult


class _NamespaceIndex:
    """One FAISS index + id/metadata bookkeeping for a single namespace."""

    def __init__(self, dimensions: int):
        import faiss

        self.dimensions = dimensions
        # IndexFlatIP = exact inner-product search. We normalize vectors on
        # insert so inner product == cosine similarity. Exact search is
        # fine at dev scale (thousands of vectors); Qdrant takes over for
        # production-scale approximate search.
        self.index = faiss.IndexFlatIP(dimensions)
        self.ids: list[str] = []
        self.metadata: dict[str, dict] = {}

    @staticmethod
    def _normalize(vector: list[float]) -> np.ndarray:
        arr = np.array(vector, dtype="float32")
        norm = np.linalg.norm(arr)
        return arr / norm if norm > 0 else arr

    def upsert(self, records: list[VectorRecord]) -> None:
        vectors = np.stack([self._normalize(r.vector) for r in records])
        self.index.add(vectors)
        for r in records:
            self.ids.append(r.id)
            self.metadata[r.id] = r.metadata

    def search(self, query_vector: list[float], top_k: int, metadata_filter: dict | None) -> list[VectorSearchResult]:
        if self.index.ntotal == 0:
            return []
        query = self._normalize(query_vector).reshape(1, -1)
        # Over-fetch when filtering, since some hits may be excluded by
        # metadata_filter after the fact — FAISS itself has no filter concept.
        fetch_k = min(self.index.ntotal, top_k * 5 if metadata_filter else top_k)
        scores, indices = self.index.search(query, fetch_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            record_id = self.ids[idx]
            meta = self.metadata[record_id]
            if metadata_filter and not all(meta.get(k) == v for k, v in metadata_filter.items()):
                continue
            results.append(VectorSearchResult(id=record_id, score=float(score), metadata=meta))
            if len(results) >= top_k:
                break
        return results

    def delete(self, ids: list[str]) -> None:
        # FAISS's IndexFlatIP has no native delete; simplest correct
        # approach at dev scale is a full rebuild excluding deleted ids.
        import faiss

        keep = [(i, rid) for i, rid in enumerate(self.ids) if rid not in ids]
        if len(keep) == len(self.ids):
            return
        new_index = faiss.IndexFlatIP(self.dimensions)
        if keep:
            vectors = np.stack([self.index.reconstruct(i) for i, _ in keep])
            new_index.add(vectors)
        self.index = new_index
        self.ids = [rid for _, rid in keep]
        self.metadata = {rid: self.metadata[rid] for rid in self.ids}


class FaissVectorStore(IVectorStore):
    def __init__(self, dimensions: int):
        self._dimensions = dimensions
        self._namespaces: dict[str, _NamespaceIndex] = {}

    def _get_namespace(self, namespace: str) -> _NamespaceIndex:
        if namespace not in self._namespaces:
            self._namespaces[namespace] = _NamespaceIndex(self._dimensions)
        return self._namespaces[namespace]

    async def upsert(self, namespace: str, records: list[VectorRecord]) -> None:
        self._get_namespace(namespace).upsert(records)

    async def search(
        self, namespace: str, query_vector: list[float], top_k: int = 5, metadata_filter: dict | None = None
    ) -> list[VectorSearchResult]:
        return self._get_namespace(namespace).search(query_vector, top_k, metadata_filter)

    async def delete(self, namespace: str, ids: list[str]) -> None:
        self._get_namespace(namespace).delete(ids)
