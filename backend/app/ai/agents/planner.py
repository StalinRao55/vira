"""
ai/agents/planner.py

Why this file exists:
    Single responsibility: look at the user's message and decide which
    downstream agents (memory / research / tool) are actually needed —
    running every agent on every message would be slow and expensive for
    no benefit on a simple "hello". The plan is a short ordered list of
    agent names; CoordinatorAgent executes it.

How it communicates with other modules:
    - Depends on ai/providers/base.ILLMProvider (interface)
    - Its output (context.plan) is consumed by ai/agents/coordinator.py
"""

import json
import logging

from app.ai.agents.base import AgentContext, AgentResult, AgentType, IAgent
from app.ai.providers.base import ChatTurn, ILLMProvider

logger = logging.getLogger(__name__)

_VALID_STEPS = {"memory", "research", "tool"}

_PLANNING_PROMPT = """You are a planning module for an AI assistant. Given the user's message, \
decide which of these steps are needed before generating a response:
- "memory": look up remembered facts/preferences about the user
- "research": look up external/current information (only if the question needs facts beyond general knowledge)
- "tool": perform a calculation or structured operation

Respond with ONLY a JSON array of step names needed, in execution order. Use an empty array \
if the message can be answered directly with no lookups (e.g. greetings, opinions, general knowledge).

User message: {message}

JSON array:"""


class PlannerAgent(IAgent):
    def __init__(self, llm_provider: ILLMProvider):
        self._llm_provider = llm_provider

    @property
    def agent_type(self) -> AgentType:
        return AgentType.PLANNER

    async def run(self, context: AgentContext) -> AgentResult:
        try:
            prompt = _PLANNING_PROMPT.format(message=context.user_message[:1000])
            chunks = [
                chunk.text
                async for chunk in self._llm_provider.stream_completion(
                    messages=[ChatTurn(role="user", content=prompt)], model="gemini-3-flash", temperature=0.0
                )
            ]
            raw = "".join(chunks).strip()
            plan = self._parse_plan(raw)
        except Exception:
            logger.exception("Planning failed; falling back to no-op plan")
            plan = []

        context.plan = plan
        return AgentResult(agent_type=self.agent_type, output=json.dumps(plan), metadata={"steps": len(plan)})

    @staticmethod
    def _parse_plan(raw: str) -> list[str]:
        # Models sometimes wrap JSON in markdown fences despite instructions
        # — strip those defensively rather than failing the whole plan.
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            return []
        if not isinstance(parsed, list):
            return []
        return [step for step in parsed if step in _VALID_STEPS]
