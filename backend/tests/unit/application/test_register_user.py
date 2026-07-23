"""
tests/unit/application/test_register_user.py

Why this file exists:
    Demonstrates the payoff of the repository interface: we test the
    registration business rule (reject duplicate emails, hash the
    password) WITHOUT a running Postgres instance, by injecting a trivial
    in-memory fake that implements IUserRepository.
"""

import pytest

from app.application.use_cases.register_user import RegisterUserUseCase
from app.domain.entities.user import User
from app.domain.exceptions.auth_exceptions import EmailAlreadyRegisteredError
from app.domain.repositories.user_repository import IUserRepository


class InMemoryUserRepository(IUserRepository):
    def __init__(self):
        self._users: dict[str, User] = {}

    async def get_by_id(self, user_id):
        return next((u for u in self._users.values() if u.id == user_id), None)

    async def get_by_email(self, email):
        return self._users.get(email)

    async def get_by_oauth_id(self, provider, oauth_id):
        return next(
            (u for u in self._users.values() if u.oauth_provider == provider and u.oauth_id == oauth_id),
            None,
        )

    async def create(self, user):
        self._users[user.email] = user
        return user

    async def update(self, user):
        self._users[user.email] = user
        return user


@pytest.mark.asyncio
async def test_register_new_user_succeeds():
    repo = InMemoryUserRepository()
    use_case = RegisterUserUseCase(repo)

    user = await use_case.execute(email="alice@example.com", password="supersecret123")

    assert user.email == "alice@example.com"
    assert user.hashed_password != "supersecret123"  # must be hashed, not plaintext


@pytest.mark.asyncio
async def test_register_duplicate_email_raises():
    repo = InMemoryUserRepository()
    use_case = RegisterUserUseCase(repo)
    await use_case.execute(email="bob@example.com", password="password123")

    with pytest.raises(EmailAlreadyRegisteredError):
        await use_case.execute(email="bob@example.com", password="different456")
