"""
application/use_cases/register_user.py

Why this file exists:
    Encapsulates the "register a new user with email/password" business
    workflow in one testable, framework-agnostic class. The router that
    calls this doesn't know or care how registration works internally.

How it communicates with other modules:
    - Depends on IUserRepository (interface, injected)
    - Depends on core/security.hash_password
    - Raises EmailAlreadyRegisteredError (domain/exceptions), caught by
      api/v1/routers/auth.py
"""

import logging

from app.core.security import hash_password
from app.domain.entities.user import User
from app.domain.exceptions.auth_exceptions import EmailAlreadyRegisteredError
from app.domain.repositories.user_repository import IUserRepository

logger = logging.getLogger(__name__)


class RegisterUserUseCase:
    def __init__(self, user_repository: IUserRepository):
        self._user_repository = user_repository

    async def execute(self, email: str, password: str) -> User:
        existing = await self._user_repository.get_by_email(email)
        if existing is not None:
            logger.info("Registration attempt with existing email: %s", email)
            raise EmailAlreadyRegisteredError(email)

        user = User(email=email, hashed_password=hash_password(password))
        created_user = await self._user_repository.create(user)
        logger.info("User registered: %s", created_user.id)
        return created_user
