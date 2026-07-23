"""
ai/agents/memory_agent.py

Why this file exists:
    Single responsibility: retrieve relevant long-term memories for the
    current message and add them to the shared context. Thin by design —
    all the actual ranking logic lives in LongTermMemoryManager (Phase 6);
    this agent just adapts that manager to the IAgent contract so the
    coordinator can invoke it uniformly with the other agents.
"""

import logging

from app.ai.agents.base import AgentContext, AgentResult, AgentType, IAgent
from app.ai.memory.long_term import LongTermMemoryManager

logger = logging.getLogger(__name__)


class MemoryAgent(IAgent):
    def __init__(self, long_term_memory: LongTermMemoryManager):
        self._long_term_memory = long_term_memory

    @property
    def agent_type(self) -> AgentType:
        return AgentType.MEMORY

    async def run(self, context: AgentContext) -> AgentResult:
        try:
            memories = await self._long_term_memory.recall(context.user_id, query=context.user_message, top_k=5)
        except Exception as exc:
            logger.exception("Memory recall failed")
            return AgentResult(agent_type=self.agent_type, output="", success=False, error=str(exc))

        if not memories:
            return AgentResult(agent_type=self.agent_type, output="", metadata={"count": 0})

        summary = "\n".join(f"- {m.content}" for m in memories)
        context.accumulated_context["memory"] = summary
        return AgentResult(agent_type=self.agent_type, output=summary, metadata={"count": len(memories)})
