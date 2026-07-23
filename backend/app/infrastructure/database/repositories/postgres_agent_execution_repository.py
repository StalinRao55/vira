"""
infrastructure/database/repositories/postgres_agent_execution_repository.py

Why this file exists:
    ORM model + repository implementation for agent execution history,
    bundled in one file (rather than a separate models/ file) to keep pace
    given this is a supporting/logging entity, not a core aggregate.
"""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text, func, select
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.agent_execution import AgentExecution
from app.domain.repositories.agent_execution_repository import IAgentExecutionRepository
from app.infrastructure.database.base import Base


class AgentExecutionModel(Base):
    __tablename__ = "agent_executions"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("messages.id"), index=True, nullable=False)
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    input_summary: Mapped[str] = mapped_column(Text, nullable=False)
    output_summary: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)


class PostgresAgentExecutionRepository(IAgentExecutionRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, execution: AgentExecution) -> AgentExecution:
        model = AgentExecutionModel(
            id=execution.id,
            message_id=execution.message_id,
            agent_type=execution.agent_type,
            input_summary=execution.input_summary,
            output_summary=execution.output_summary,
            status=execution.status,
            duration_ms=execution.duration_ms,
        )
        self._session.add(model)
        await self._session.commit()
        return execution

    async def list_by_message(self, message_id: uuid.UUID) -> list[AgentExecution]:
        stmt = select(AgentExecutionModel).where(AgentExecutionModel.message_id == message_id)
        result = await self._session.execute(stmt)
        return [
            AgentExecution(
                id=m.id,
                message_id=m.message_id,
                agent_type=m.agent_type,
                input_summary=m.input_summary,
                output_summary=m.output_summary,
                status=m.status,
                duration_ms=m.duration_ms,
                created_at=m.created_at,
            )
            for m in result.scalars().all()
        ]
