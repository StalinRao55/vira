"""
infrastructure/storage/factory.py

Why this file exists:
    Config-driven storage backend selection, consistent with every other
    factory in the codebase.
"""

from functools import lru_cache

from app.infrastructure.storage.base import IFileStorage
from app.infrastructure.storage.local_file_storage import LocalFileStorage


@lru_cache
def get_file_storage() -> IFileStorage:
    return LocalFileStorage()
