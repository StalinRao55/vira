"""
ai/tools/registry.py

Why this file exists:
    Implements Phase 8's IToolExecutor by holding a name->Tool mapping and
    dispatching execute() calls to the right one. This is the concrete
    answer to "support future tools without modifying the framework" —
    adding tool #11 is `registry.register(NewTool())`, full stop. Nothing
    in ai/agents/* or application/use_cases/* changes.
"""

import logging

from app.ai.tools.base import IToolExecutor, ToolCallResult
from app.ai.tools.tool import Tool

logger = logging.getLogger(__name__)


class ToolRegistry(IToolExecutor):
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool
        logger.info("Registered tool: %s", tool.name)

    async def execute(self, tool_name: str, arguments: dict) -> ToolCallResult:
        tool = self._tools.get(tool_name)
        if tool is None:
            return ToolCallResult(tool_name=tool_name, output="", success=False, error=f"Unknown tool: {tool_name}")

        result = await tool.execute(arguments)
        return ToolCallResult(tool_name=tool_name, output=result.output, success=result.success, error=result.error)

    def available_tools(self) -> list[str]:
        return list(self._tools.keys())

    def descriptions(self) -> dict[str, str]:
        return {name: tool.description for name, tool in self._tools.items()}
