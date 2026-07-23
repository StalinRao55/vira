"""
application/use_cases/login_user.py

Why this file exists:
    Encapsulates the "verify credentials, issue tokens" workflow. Keeping
    this separate from the router means the same logic can be reused (e.g.
    by an internal admin tool) without duplicating it.

How it communicates with other modules:
    - Depends on IUserRepository (interface, injected)
    - Depends on core/security (verify_password, create_access_token,
      create_refresh_token)
    - Raises InvalidCredentialsError (domain/exceptions)
"""

import logging
from dataclasses import dataclass

from app.core.security import create_access_token, create_refresh_token, verify_password
from app.domain.exceptions.auth_exceptions import InvalidCredentialsError
from app.domain.repositories.user_repository import IUserRepository

logger = logging.getLogger(__name__)


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str


class LoginUserUseCase:
    def __init__(self, user_repository: IUserRepository):
        self._user_repository = user_repository

    async def execute(self, email: str, password: str) -> TokenPair:
        user = await self._user_repository.get_by_email(email)

        # Deliberately identical error for "no such user" and "wrong
        # password" — this prevents leaking which emails are registered.
        if user is None or user.hashed_password is None:
            raise InvalidCredentialsError()

        if not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()

        logger.info("User logged in: %s", user.id)
        return TokenPair(
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(str(user.id)),
        )
