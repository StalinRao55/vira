"""
infrastructure/storage/local_file_storage.py

Why this file exists:
    Dev-time IFileStorage implementation — writes to a local directory.
    Documented limitation: doesn't work across multiple server instances;
    Phase 13 swaps to S3-compatible storage behind the same interface.
"""

import asyncio
from pathlib import Path

from app.infrastructure.storage.base import IFileStorage


class LocalFileStorage(IFileStorage):
    def __init__(self, base_dir: str = "./storage/uploads"):
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve(self, path: str) -> Path:
        resolved = (self._base_dir / path).resolve()
        if not str(resolved).startswith(str(self._base_dir.resolve())):
            raise ValueError(f"Invalid storage path: {path}")
        return resolved

    async def save(self, path: str, content: bytes) -> str:
        full_path = self._resolve(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(full_path.write_bytes, content)
        return path

    async def read(self, path: str) -> bytes:
        full_path = self._resolve(path)
        return await asyncio.to_thread(full_path.read_bytes)

    async def delete(self, path: str) -> None:
        full_path = self._resolve(path)
        if full_path.exists():
            await asyncio.to_thread(full_path.unlink)
