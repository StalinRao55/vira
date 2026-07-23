"""
infrastructure/database/base.py

Why this file exists:
    Sets up the async SQLAlchemy engine and session factory once, so every
    repository gets a consistent, connection-pooled session instead of each
    one opening its own connection.

How it communicates with other modules:
    - infrastructure/database/repositories/* receive an AsyncSession via
      this file's get_session (wired through api/v1/dependencies.py)
    - infrastructure/database/models/* declare tables against `Base`
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Shared declarative base — every ORM model inherits from this."""


engine = create_async_engine(settings.database_url, echo=(settings.environment == "development"))

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields a session and guarantees it's closed after
    the request, even if an exception is raised."""
    async with async_session_factory() as session:
        yield session
