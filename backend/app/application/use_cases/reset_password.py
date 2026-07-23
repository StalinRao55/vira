"""
application/use_cases/reset_password.py

Reset user password using a token.
"""

import logging

from app.core.security import hash_password
from app.domain.exceptions.auth_exceptions import InvalidTokenError
from app.domain.repositories.password_reset_repository import IPasswordResetRepository
from app.domain.repositories.user_repository import IUserRepository

logger = logging.getLogger(__name__)


class ResetPasswordUseCase:
    """Reset a user's password using a reset token."""

    def __init__(self, user_repository: IUserRepository, reset_repository: IPasswordResetRepository):
        self._user_repository = user_repository
        self._reset_repository = reset_repository

    async def execute(self, token: str, new_password: str) -> None:
        """Validate the reset token and update the user's password."""
        # Get the reset token record
        reset_token = await self._reset_repository.get_by_token(token)
        if reset_token is None or reset_token.is_expired():
            logger.warning("Invalid or expired password reset token")
            raise InvalidTokenError("Invalid or expired reset token")

        # Get the user
        user = await self._user_repository.get_by_id(reset_token.user_id)
        if user is None:
            raise InvalidTokenError("User not found")

        # Update password
        user.hashed_password = hash_password(new_password)
        await self._user_repository.update(user)

        # Delete the token
        await self._reset_repository.delete_by_token(token)

        logger.info("Password reset for user: %s", user.id)
