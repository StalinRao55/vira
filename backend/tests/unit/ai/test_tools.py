"""
tests/unit/ai/test_tools.py

Why this file exists:
    Verifies the calculator's safe evaluation (including that it REJECTS
    unsafe input), the datetime tool, the python sandbox (real subprocess
    execution, real timeout/error handling), and that the registry
    correctly dispatches by name and reports unknown tools as failures
    rather than raising.
"""

import pytest

from app.ai.tools.implementations.calculator import CalculatorTool
from app.ai.tools.implementations.datetime_tool import DateTimeTool
from app.ai.tools.implementations.python_sandbox import PythonSandboxTool
from app.ai.tools.registry import ToolRegistry


@pytest.mark.asyncio
async def test_calculator_evaluates_arithmetic():
    result = await CalculatorTool().execute({"expression": "2 + 3 * 4"})
    assert result.success
    assert result.output == "14"


@pytest.mark.asyncio
async def test_calculator_rejects_unsafe_input():
    # Attempting to call a function must fail, not execute — this is the
    # entire point of using ast instead of eval().
    result = await CalculatorTool().execute({"expression": "__import__('os').system('echo pwned')"})
    assert not result.success


@pytest.mark.asyncio
async def test_datetime_tool_returns_current_time():
    result = await DateTimeTool().execute({})
    assert result.success
    assert "UTC" in result.output


@pytest.mark.asyncio
async def test_python_sandbox_executes_and_captures_output():
    result = await PythonSandboxTool().execute({"code": "print(2 + 2)"})
    assert result.success
    assert result.output.strip() == "4"


@pytest.mark.asyncio
async def test_python_sandbox_reports_errors_without_crashing():
    result = await PythonSandboxTool().execute({"code": "raise ValueError('boom')"})
    assert not result.success
    assert "boom" in result.error


@pytest.mark.asyncio
async def test_registry_dispatches_by_name():
    registry = ToolRegistry()
    registry.register(CalculatorTool())

    result = await registry.execute("calculator", {"expression": "10 / 2"})

    assert result.success
    assert result.output == "5.0"
    assert "calculator" in registry.available_tools()


@pytest.mark.asyncio
async def test_registry_handles_unknown_tool_gracefully():
    registry = ToolRegistry()
    result = await registry.execute("nonexistent_tool", {})
    assert not result.success
    assert "Unknown tool" in result.error
