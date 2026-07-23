"""
infrastructure/storage/base.py

Why this file exists:
    Contract for saving/reading/deleting uploaded files, independent of
    where they actually live. Dev uses local disk; Phase 13 swaps in
    S3-compatible/Supabase Storage behind this same interface with zero
    application-layer changes — same pattern as IVectorStore.
"""

from abc import ABC, abstractmethod


class IFileStorage(ABC):
    @abstractmethod
    async def save(self, path: str, content: bytes) -> str: ...

    @abstractmethod
    async def read(self, path: str) -> bytes: ...

    @abstractmethod
    async def delete(self, path: str) -> None: ...
