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

from app.ai.embeddings.factory import get_embedding_provider
from app.infrastructure.vector_store.base import IVectorStore
from app.infrastructure.vector_store.faiss_vector_store import FaissVectorStore


@lru_cache
def get_vector_store() -> IVectorStore:
    """Cached (singleton) for the lifetime of the process. Dimensions are
    taken from whatever embedding provider factory.py actually selected
    (gemini → 768, mock → 32), so the FAISS index always matches the
    vectors it stores."""
    embedding_provider = get_embedding_provider()
    dimensions = embedding_provider.dimensions
    return FaissVectorStore(dimensions=dimensions)
