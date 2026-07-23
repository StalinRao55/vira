"""
ai/agents/base.py

Why this file exists:
    Defines the contract every agent implements: run(context) -> AgentResult.
    AgentContext is the shared, growing bag of state a pipeline run
    accumulates as it passes through Planner -> Research/Memory/Tool ->
    Response — each agent reads what it needs and adds its own findings to
    `accumulated_context`, so downstream agents (especially ResponseAgent)
    see everything gathered so far without a rigid fixed schema.

How it communicates with other modules:
    - Implemented by every file in ai/agents/
    - AgentContext/AgentResult are constructed and consumed by
      ai/agents/coordinator.py and application/use_cases/run_agent_pipeline.py
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID

from app.ai.providers.base import ChatTurn


class AgentType(str, Enum):
    PLANNER = "planner"
    RESEARCH = "research"
    MEMORY = "memory"
    TOOL = "tool"
    RESPONSE = "response"
    COORDINATOR = "coordinator"


@dataclass
class AgentContext:
    user_id: UUID
    conversation_id: UUID
    user_message: str
    history: list[ChatTurn] = field(default_factory=list)
    # Free-form bag other agents write findings into, keyed by their own
    # name (e.g. "memory", "research"). ResponseAgent reads all of it.
    accumulated_context: dict[str, str] = field(default_factory=dict)
    # Set by PlannerAgent; consumed by CoordinatorAgent to know what to run.
    plan: list[str] = field(default_factory=list)


@dataclass
class AgentResult:
    agent_type: AgentType
    output: str
    metadata: dict = field(default_factory=dict)
    success: bool = True
    error: str | None = None


class IAgent(ABC):
    @property
    @abstractmethod
    def agent_type(self) -> AgentType: ...

    @abstractmethod
    async def run(self, context: AgentContext) -> AgentResult:
        """Executes this agent's responsibility against the shared context
        and returns a result. Implementations should catch their own
        exceptions and return success=False rather than raising, so one
        failing agent doesn't take down the whole pipeline."""
        ...
