"""
application/use_cases/request_password_reset.py

Request a password reset via email.
"""

import logging
import secrets
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.domain.exceptions.auth_exceptions import UserNotFoundError
from app.domain.repositories.password_reset_repository import IPasswordResetRepository
from app.domain.repositories.user_repository import IUserRepository

logger = logging.getLogger(__name__)


class RequestPasswordResetUseCase:
    """Request a password reset. Generates a token and stores it."""

    def __init__(self, user_repository: IUserRepository, reset_repository: IPasswordResetRepository):
        self._user_repository = user_repository
        self._reset_repository = reset_repository

    async def execute(self, email: str) -> str | None:
        """Generate a reset token and store it for the user.
        
        Returns the reset token (in production, this would be sent via email).
        Returns None if user doesn't exist (to avoid leaking email existence).
        """
        user = await self._user_repository.get_by_email(email)
        if user is None:
            # Don't leak whether the email exists
            logger.info("Password reset requested for non-existent email: %s", email)
            return None

        # Generate a secure token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        # Delete any existing reset tokens for this user
        await self._reset_repository.delete_by_user_id(user.id)

        # Store the new token
        await self._reset_repository.create(user.id, token, expires_at)
        logger.info("Generated password reset token for user: %s", user.id)

        # In production:
        # - Send email with reset link containing the token
        # - Something like: /reset-password?token=<token>
        return token

