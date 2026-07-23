"""
infrastructure/database/repositories/postgres_password_reset_repository.py

Postgres implementation of password reset token storage.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.password_reset_repository import (
    IPasswordResetRepository,
    PasswordResetToken,
)
from app.infrastructure.database.models.password_reset_model import PasswordResetTokenModel


class PostgresPasswordResetRepository(IPasswordResetRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, user_id: UUID, token: str, expires_at: datetime) -> PasswordResetToken:
        model = PasswordResetTokenModel(user_id=user_id, token=token, expires_at=expires_at)
        self._session.add(model)
        await self._session.flush()
        return PasswordResetToken(
            id=model.id,
            user_id=model.user_id,
            token=model.token,
            expires_at=model.expires_at,
        )

    async def get_by_token(self, token: str) -> PasswordResetToken | None:
        result = await self._session.execute(
            select(PasswordResetTokenModel).where(PasswordResetTokenModel.token == token)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return PasswordResetToken(
            id=model.id,
            user_id=model.user_id,
            token=model.token,
            expires_at=model.expires_at,
        )

    async def delete_by_user_id(self, user_id: UUID) -> None:
        await self._session.execute(delete(PasswordResetTokenModel).where(PasswordResetTokenModel.user_id == user_id))

    async def delete_by_token(self, token: str) -> None:
        await self._session.execute(delete(PasswordResetTokenModel).where(PasswordResetTokenModel.token == token))
