"""
ai/tools/base.py

Why this file exists:
    ResearchAgent and ToolAgent (Phase 8) need SOMETHING to call tools
    through, but the full Tool Execution Framework (calculator, web search,
    python sandbox, etc.) is Phase 9's job. Rather than couple agents to a
    not-yet-built concrete system, this defines the minimal interface both
    phases agree on now. Phase 9 will add ToolRegistry and the individual
    tool implementations behind this same IToolExecutor contract — the
    agents built in this phase will not need to change.

How it communicates with other modules:
    - Implemented (fully) by Phase 9's ToolRegistry
    - Implemented (minimally, for testing) by StubToolExecutor below
    - Consumed by ai/agents/research.py and ai/agents/tool_agent.py
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ToolCallResult:
    tool_name: str
    output: str
    success: bool
    error: str | None = None


class IToolExecutor(ABC):
    @abstractmethod
    async def execute(self, tool_name: str, arguments: dict) -> ToolCallResult: ...

    @abstractmethod
    def available_tools(self) -> list[str]:
        """Names of tools currently registered — PlannerAgent uses this to
        avoid planning a step for a tool that doesn't exist."""
        ...
