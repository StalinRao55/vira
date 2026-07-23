"""
api/v1/routers/analytics.py

Why this file exists:
    Exposes usage analytics: a per-user summary (token usage, cost
    estimation, latency — e.g. for a "usage" settings panel). Extends
    naturally to an admin-wide view since require_admin is already wired.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, get_session
from app.domain.entities.user import User
from app.infrastructure.database.repositories.postgres_usage_repository import PostgresUsageRepository

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/usage")
async def get_usage_summary(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    days: int = Query(default=30, ge=1, le=365),
) -> dict:
    repo = PostgresUsageRepository(session)
    return await repo.summary_for_user(current_user.id, days=days)
