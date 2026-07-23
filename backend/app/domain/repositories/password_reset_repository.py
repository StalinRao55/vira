"""
domain/repositories/password_reset_repository.py

Interface for password reset token storage.
"""

from datetime import datetime
from uuid import UUID


class PasswordResetToken:
    def __init__(self, id: UUID, user_id: UUID, token: str, expires_at: datetime):
        self.id = id
        self.user_id = user_id
        self.token = token
        self.expires_at = expires_at

    def is_expired(self) -> bool:
        from datetime import timezone
        return datetime.now(timezone.utc) > self.expires_at


class IPasswordResetRepository(ABC):
    @abstractmethod
    async def create(self, user_id: UUID, token: str, expires_at: datetime) -> PasswordResetToken: ...

    @abstractmethod
    async def get_by_token(self, token: str) -> PasswordResetToken | None: ...

    @abstractmethod
    async def delete_by_user_id(self, user_id: UUID) -> None: ...

    @abstractmethod
    async def delete_by_token(self, token: str) -> None: ...
