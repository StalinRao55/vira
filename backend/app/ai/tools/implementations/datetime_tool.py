"""
ai/tools/implementations/datetime_tool.py

Why this file exists:
    Gives the model access to the actual current date/time — LLMs have no
    reliable internal clock, so this is a small but genuinely necessary
    tool for any date-relative question ("what's next Friday").
"""

from datetime import datetime, timezone

from app.ai.tools.tool import Tool, ToolResult


class DateTimeTool(Tool):
    @property
    def name(self) -> str:
        return "current_datetime"

    @property
    def description(self) -> str:
        return "Returns the current date and time in UTC."

    async def execute(self, arguments: dict) -> ToolResult:
        now = datetime.now(timezone.utc)
        return ToolResult(output=now.strftime("%Y-%m-%d %H:%M:%S UTC (%A)"))
