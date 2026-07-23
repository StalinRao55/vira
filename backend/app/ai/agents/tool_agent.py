"""
ai/agents/tool_agent.py

Why this file exists:
    Single responsibility: execute a structured tool call (calculator,
    date/time, etc.) identified by the planner, via IToolExecutor.
    Distinct from ResearchAgent even though both use tools — this one
    handles deterministic/structured operations, ResearchAgent handles
    information lookup. Splitting them keeps each agent's prompt/logic
    focused rather than one "do everything with tools" agent.
"""

import logging
import re

from app.ai.agents.base import AgentContext, AgentResult, AgentType, IAgent
from app.ai.tools.base import IToolExecutor

logger = logging.getLogger(__name__)

_CALCULATION_PATTERN = re.compile(r"[\d\s+\-*/().]+")


class ToolAgent(IAgent):
    def __init__(self, tool_executor: IToolExecutor):
        self._tool_executor = tool_executor

    @property
    def agent_type(self) -> AgentType:
        return AgentType.TOOL

    async def run(self, context: AgentContext) -> AgentResult:
        # Minimal heuristic tool selection for now: detect an arithmetic
        # expression and route to "calculator". Phase 9 gives this real
        # tool-selection logic (e.g. an LLM function-calling pass across
        # ALL registered tools); this agent's contract doesn't change.
        match = _CALCULATION_PATTERN.search(context.user_message)
        if match and any(ch.isdigit() for ch in match.group()) and "calculator" in self._tool_executor.available_tools():
            result = await self._tool_executor.execute("calculator", {"expression": match.group().strip()})
            if result.success:
                context.accumulated_context["tool"] = f"Calculator result: {result.output}"
                return AgentResult(agent_type=self.agent_type, output=result.output)
            return AgentResult(agent_type=self.agent_type, output="", success=False, error=result.error)

        return AgentResult(agent_type=self.agent_type, output="", metadata={"reason": "no applicable tool detected"})
