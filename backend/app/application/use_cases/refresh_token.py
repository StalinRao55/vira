"""
application/use_cases/refresh_token.py

Why this file exists:
    Implements token rotation: given a valid refresh token, verify the user
    still exists and issue a fresh access token (and, per rotation best
    practice, a fresh refresh token too — reduces the blast radius if a
    refresh token is ever leaked).

How it communicates with other modules:
    - Depends on IUserRepository (interface, injected)
    - Depends on core/security (decode_token, create_access_token,
      create_refresh_token)
    - Raises InvalidTokenError / UserNotFoundError (domain/exceptions)
"""

import logging
from uuid import UUID

import jwt

from app.core.security import TokenType, create_access_token, create_refresh_token, decode_token
from app.domain.exceptions.auth_exceptions import InvalidTokenError, UserNotFoundError
from app.domain.repositories.user_repository import IUserRepository
from app.application.use_cases.login_user import TokenPair

logger = logging.getLogger(__name__)


class RefreshTokenUseCase:
    def __init__(self, user_repository: IUserRepository):
        self._user_repository = user_repository

    async def execute(self, refresh_token: str) -> TokenPair:
        try:
            user_id_str = decode_token(refresh_token, expected_type=TokenType.REFRESH)
        except jwt.PyJWTError as exc:
            raise InvalidTokenError(str(exc)) from exc

        user = await self._user_repository.get_by_id(UUID(user_id_str))
        if user is None:
            raise UserNotFoundError()

        logger.info("Token refreshed for user: %s", user.id)
        return TokenPair(
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(str(user.id)),
        )
