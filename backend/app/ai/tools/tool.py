"""
ai/tools/tool.py

Why this file exists:
    The actual "Tool -> execute() -> Result" contract from the spec, one
    level more specific than IToolExecutor (Phase 8's minimal seam).
    ToolRegistry (this phase) implements IToolExecutor by dispatching to
    registered Tool instances — agents from Phase 8 need no changes.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ToolResult:
    output: str
    success: bool = True
    error: str | None = None


class Tool(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human/LLM-readable description — used for future function-calling
        style tool selection."""
        ...

    @abstractmethod
    async def execute(self, arguments: dict) -> ToolResult: ...
