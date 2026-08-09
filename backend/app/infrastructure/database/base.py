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


# SQLite needs check_same_thread=False for async usage
_connect_args = {}
if settings.database_url.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_async_engine(
    settings.database_url,
    echo=(settings.environment == "development"),
    connect_args=_connect_args,
)

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    """Create all tables if they don't exist yet.

    For SQLite local dev this replaces running Alembic migrations.
    In production (Postgres) Alembic handles schema migrations instead.
    """
    # Import all models so their metadata is registered with Base
    import app.infrastructure.database.models.user_model  # noqa: F401
    import app.infrastructure.database.models.chat_models  # noqa: F401
    import app.infrastructure.database.models.memory_model  # noqa: F401
    import app.infrastructure.database.models.document_models  # noqa: F401
    import app.infrastructure.database.models.password_reset_model  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields a session and guarantees it's closed after
    the request, even if an exception is raised."""
    async with async_session_factory() as session:
        yield session
