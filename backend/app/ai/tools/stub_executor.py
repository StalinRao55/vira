"""
ai/tools/stub_executor.py

Why this file exists:
    Lets the agent framework (Phase 8) be built and tested end-to-end
    before the real Tool Execution Framework (Phase 9) exists. Registering
    a couple of trivial callables here proves the IToolExecutor contract
    works; Phase 9 replaces this with ToolRegistry wired to real tools,
    with zero changes needed to any agent.
"""

from collections.abc import Awaitable, Callable

from app.ai.tools.base import IToolExecutor, ToolCallResult

_ToolFunc = Callable[[dict], Awaitable[str]]


class StubToolExecutor(IToolExecutor):
    def __init__(self, tools: dict[str, _ToolFunc] | None = None):
        self._tools = tools or {}

    def register(self, name: str, func: _ToolFunc) -> None:
        self._tools[name] = func

    async def execute(self, tool_name: str, arguments: dict) -> ToolCallResult:
        if tool_name not in self._tools:
            return ToolCallResult(tool_name=tool_name, output="", success=False, error=f"Unknown tool: {tool_name}")
        try:
            output = await self._tools[tool_name](arguments)
            return ToolCallResult(tool_name=tool_name, output=output, success=True)
        except Exception as exc:
            return ToolCallResult(tool_name=tool_name, output="", success=False, error=str(exc))

    def available_tools(self) -> list[str]:
        return list(self._tools.keys())
