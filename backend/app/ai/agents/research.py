"""
ai/agents/research.py

Why this file exists:
    Single responsibility: gather external/current information the model's
    own knowledge can't provide, by invoking a "web_search"-shaped tool
    through IToolExecutor. Depends only on the interface — Phase 9's real
    web search tool slots in with no change here.
"""

import logging

from app.ai.agents.base import AgentContext, AgentResult, AgentType, IAgent
from app.ai.tools.base import IToolExecutor

logger = logging.getLogger(__name__)


class ResearchAgent(IAgent):
    def __init__(self, tool_executor: IToolExecutor):
        self._tool_executor = tool_executor

    @property
    def agent_type(self) -> AgentType:
        return AgentType.RESEARCH

    async def run(self, context: AgentContext) -> AgentResult:
        if "web_search" not in self._tool_executor.available_tools():
            return AgentResult(
                agent_type=self.agent_type, output="", success=False, error="web_search tool not available"
            )

        result = await self._tool_executor.execute("web_search", {"query": context.user_message})
        if not result.success:
            return AgentResult(agent_type=self.agent_type, output="", success=False, error=result.error)

        context.accumulated_context["research"] = result.output
        return AgentResult(agent_type=self.agent_type, output=result.output)
