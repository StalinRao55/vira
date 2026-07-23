"""
infrastructure/vector_store/factory.py

Why this file exists:
    Config-driven vector store selection, matching the pattern used for
    LLM and embedding providers. Also owns a critical detail: FaissVectorStore
    holds its index in process memory, so it MUST be a singleton — a new
    instance per request would silently lose every previously stored
    vector. This factory guarantees exactly one instance per process.

How it communicates with other modules:
    - Instantiates FaissVectorStore (dev) / would instantiate
      QdrantVectorStore (prod) based on settings
    - Injected into ai/memory/long_term.py via api/v1/dependencies.py
"""

from functools import lru_cache

from app.core.config import settings
from app.infrastructure.vector_store.base import IVectorStore
from app.infrastructure.vector_store.faiss_vector_store import FaissVectorStore

_GEMINI_EMBEDDING_DIMENSIONS = 768
_MOCK_EMBEDDING_DIMENSIONS = 32


@lru_cache
def get_vector_store() -> IVectorStore:
    """Cached (singleton) for the lifetime of the process. Dimensions must
    match whatever embedding provider factory.py selects — see the
    dimensions property on IEmbeddingProvider as the source of truth in a
    future refactor; hardcoded here for clarity at this stage."""
    dimensions = _MOCK_EMBEDDING_DIMENSIONS if settings.environment == "test" else _GEMINI_EMBEDDING_DIMENSIONS
    return FaissVectorStore(dimensions=dimensions)
