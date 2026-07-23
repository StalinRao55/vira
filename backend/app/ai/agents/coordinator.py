"""
ai/agents/coordinator.py

Why this file exists:
    The only agent that knows about all the others. Runs PlannerAgent to
    get a plan, executes each planned step against the matching agent
    (memory/research/tool), then hands the accumulated context to
    ResponseAgent for the final streamed answer. Every step's AgentResult
    is yielded so the caller (RunAgentPipelineUseCase) can persist
    AgentExecution history rows without the coordinator needing to know
    anything about persistence.
"""

import logging
import time
from collections.abc import AsyncIterator

from app.ai.agents.base import AgentContext, AgentResult, AgentType, IAgent
from app.ai.agents.memory_agent import MemoryAgent
from app.ai.agents.planner import PlannerAgent
from app.ai.agents.research import ResearchAgent
from app.ai.agents.response_agent import ResponseAgent
from app.ai.agents.tool_agent import ToolAgent
from app.ai.providers.base import StreamChunk

logger = logging.getLogger(__name__)

_STEP_AGENTS = {"memory": AgentType.MEMORY, "research": AgentType.RESEARCH, "tool": AgentType.TOOL}


class CoordinatorAgent(IAgent):
    def __init__(
        self,
        planner: PlannerAgent,
        memory_agent: MemoryAgent,
        research_agent: ResearchAgent,
        tool_agent: ToolAgent,
        response_agent: ResponseAgent,
    ):
        self._planner = planner
        self._agents_by_step: dict[str, IAgent] = {
            "memory": memory_agent,
            "research": research_agent,
            "tool": tool_agent,
        }
        self._response_agent = response_agent

    @property
    def agent_type(self) -> AgentType:
        return AgentType.COORDINATOR

    async def run(self, context: AgentContext) -> AgentResult:
        raise NotImplementedError("CoordinatorAgent orchestrates a stream — use run_pipeline() instead")

    async def run_pipeline(
        self, context: AgentContext, model: str = "gemini-3-flash"
    ) -> AsyncIterator[tuple[AgentResult | None, StreamChunk | None]]:
        """Yields (AgentResult, None) for each completed planning/gathering
        step, then (None, StreamChunk) for each piece of the final
        streamed response. This dual-channel yield lets the use case
        persist execution history for the discrete steps while still
        forwarding the response as it streams."""

        plan_start = time.monotonic()
        plan_result = await self._planner.run(context)
        plan_result.metadata["duration_ms"] = int((time.monotonic() - plan_start) * 1000)
        yield plan_result, None

        for step in context.plan:
            agent = self._agents_by_step.get(step)
            if agent is None:
                continue
            step_start = time.monotonic()
            try:
                result = await agent.run(context)
            except Exception as exc:
                logger.exception("Agent step '%s' failed", step)
                result = AgentResult(agent_type=_STEP_AGENTS[step], output="", success=False, error=str(exc))
            result.metadata["duration_ms"] = int((time.monotonic() - step_start) * 1000)
            yield result, None

        async for chunk in self._response_agent.stream(context, model=model):
            yield None, chunk
