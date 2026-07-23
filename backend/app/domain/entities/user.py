"""
domain/entities/user.py

Why this file exists:
    This is what "a user" MEANS to the business logic, independent of how
    it's stored in Postgres or shaped in an API response. Use cases operate
    on this class, never on the SQLAlchemy model directly.

How it communicates with other modules:
    - infrastructure/database/repositories/postgres_user_repository.py
      converts between this entity and the SQLAlchemy UserModel
    - application/use_cases/* receive and return this entity
    - api/v1/schemas/auth_schemas.py converts this entity to a wire response
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"


@dataclass
class User:
    email: str
    role: UserRole = UserRole.USER
    hashed_password: str | None = None
    oauth_provider: str | None = None
    oauth_id: str | None = None
    is_email_verified: bool = False
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_oauth_user(self) -> bool:
        """A user registered via Google OAuth has no password of their own."""
        return self.hashed_password is None and self.oauth_provider is not None
