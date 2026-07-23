"""
domain/repositories/agent_execution_repository.py

Why this file exists:
    Contract for persisting agent pipeline execution history.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.agent_execution import AgentExecution


class IAgentExecutionRepository(ABC):
    @abstractmethod
    async def create(self, execution: AgentExecution) -> AgentExecution: ...

    @abstractmethod
    async def list_by_message(self, message_id: UUID) -> list[AgentExecution]: ...
