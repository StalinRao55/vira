"""
ai/tools/factory.py

Why this file exists:
    Single place that registers every built-in tool. Replaces Phase 8's
    StubToolExecutor now that real tools exist — agents need no changes
    since both implement the same IToolExecutor interface.
"""

from functools import lru_cache

from app.ai.tools.implementations.calculator import CalculatorTool
from app.ai.tools.implementations.datetime_tool import DateTimeTool
from app.ai.tools.implementations.document_tools import APICallerTool
from app.ai.tools.implementations.interface_tools import (
    BrowserAutomationTool,
    CalendarTool,
    EmailTool,
    WeatherTool,
    WebSearchTool,
)
from app.ai.tools.implementations.python_sandbox import PythonSandboxTool
from app.ai.tools.registry import ToolRegistry


@lru_cache
def get_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(CalculatorTool())
    registry.register(DateTimeTool())
    registry.register(PythonSandboxTool())
    registry.register(WebSearchTool())
    registry.register(WeatherTool())
    registry.register(BrowserAutomationTool())
    registry.register(EmailTool())
    registry.register(CalendarTool())
    # api_caller ships with an empty allowlist (blocks everything) until you
    # explicitly opt domains in — safer default than an open-ended fetch tool.
    registry.register(APICallerTool(allowed_domains=set()))
    return registry
