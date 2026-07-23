"""
domain/repositories/user_repository.py

Why this file exists:
    Defines the CONTRACT for persisting/retrieving users, without saying
    anything about Postgres, SQLAlchemy, or SQL. This is the seam that lets
    us unit-test use cases with an in-memory fake, and lets us swap the
    database technology without touching application logic.

How it communicates with other modules:
    - infrastructure/database/repositories/postgres_user_repository.py
      implements this interface
    - application/use_cases/* depend on IUserRepository (injected via
      core/di_container.py), never on the concrete Postgres implementation
"""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.user import User


class IUserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def get_by_oauth_id(self, provider: str, oauth_id: str) -> User | None: ...

    @abstractmethod
    async def create(self, user: User) -> User: ...

    @abstractmethod
    async def update(self, user: User) -> User: ...
