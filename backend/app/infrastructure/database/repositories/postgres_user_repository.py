"""
infrastructure/database/repositories/postgres_user_repository.py

Why this file exists:
    The ONLY place in the codebase that translates between the domain
    `User` entity and the Postgres `UserModel`. Use cases never see
    SQLAlchemy; this class is the boundary.

How it communicates with other modules:
    - Implements domain/repositories/user_repository.IUserRepository
    - Uses infrastructure/database/models/user_model.UserModel
    - Injected into use cases via api/v1/dependencies.py
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User, UserRole
from app.domain.repositories.user_repository import IUserRepository
from app.infrastructure.database.models.user_model import UserModel, UserRoleEnum


def _to_entity(model: UserModel) -> User:
    return User(
        id=model.id,
        email=model.email,
        role=UserRole(model.role.value),
        hashed_password=model.hashed_password,
        oauth_provider=model.oauth_provider,
        oauth_id=model.oauth_id,
        is_email_verified=model.is_email_verified,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class PostgresUserRepository(IUserRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        model = await self._session.get(UserModel, user_id)
        return _to_entity(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(UserModel).where(UserModel.email == email))
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def get_by_oauth_id(self, provider: str, oauth_id: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(
                UserModel.oauth_provider == provider,
                UserModel.oauth_id == oauth_id,
            )
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def create(self, user: User) -> User:
        model = UserModel(
            id=user.id,
            email=user.email,
            hashed_password=user.hashed_password,
            oauth_provider=user.oauth_provider,
            oauth_id=user.oauth_id,
            role=UserRoleEnum(user.role.value),
            is_email_verified=user.is_email_verified,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return _to_entity(model)

    async def update(self, user: User) -> User:
        model = await self._session.get(UserModel, user.id)
        if model is None:
            raise ValueError(f"User {user.id} not found for update")
        model.email = user.email
        model.hashed_password = user.hashed_password
        model.is_email_verified = user.is_email_verified
        model.role = UserRoleEnum(user.role.value)
        await self._session.commit()
        await self._session.refresh(model)
        return _to_entity(model)
