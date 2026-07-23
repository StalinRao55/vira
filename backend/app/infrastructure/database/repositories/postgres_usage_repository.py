"""
infrastructure/database/repositories/postgres_usage_repository.py

Why this file exists:
    Persists and aggregates usage records. Aggregation queries (totals by
    user) live here rather than being computed in Python after fetching
    every row — Postgres does this far more efficiently.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone

from sqlalchemy import Float, ForeignKey, Integer, String, func, select
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.usage_record import UsageRecord
from app.infrastructure.database.base import Base


class IUsageRepository(ABC):
    @abstractmethod
    async def create(self, record: UsageRecord) -> UsageRecord: ...

    @abstractmethod
    async def summary_for_user(self, user_id: uuid.UUID, days: int = 30) -> dict: ...


class UsageRecordModel(Base):
    __tablename__ = "usage_records"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
    conversation_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True, nullable=False)


class PostgresUsageRepository(IUsageRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, record: UsageRecord) -> UsageRecord:
        model = UsageRecordModel(
            id=record.id,
            user_id=record.user_id,
            conversation_id=record.conversation_id,
            provider=record.provider,
            model=record.model,
            prompt_tokens=record.prompt_tokens,
            completion_tokens=record.completion_tokens,
            latency_ms=record.latency_ms,
            estimated_cost_usd=record.estimated_cost_usd,
        )
        self._session.add(model)
        await self._session.commit()
        return record

    async def summary_for_user(self, user_id: uuid.UUID, days: int = 30) -> dict:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = select(
            func.count(UsageRecordModel.id),
            func.coalesce(func.sum(UsageRecordModel.prompt_tokens), 0),
            func.coalesce(func.sum(UsageRecordModel.completion_tokens), 0),
            func.coalesce(func.sum(UsageRecordModel.estimated_cost_usd), 0.0),
            func.coalesce(func.avg(UsageRecordModel.latency_ms), 0.0),
        ).where(UsageRecordModel.user_id == user_id, UsageRecordModel.created_at >= since)
        result = await self._session.execute(stmt)
        count, prompt_tokens, completion_tokens, cost, avg_latency = result.one()
        return {
            "period_days": days,
            "total_requests": count,
            "total_prompt_tokens": prompt_tokens,
            "total_completion_tokens": completion_tokens,
            "estimated_cost_usd": round(cost, 6),
            "average_latency_ms": round(avg_latency, 1),
        }
