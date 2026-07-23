"""
ai/agents/response_agent.py

Why this file exists:
    Single responsibility: given everything gathered by upstream agents
    (memory findings, research findings, tool results) plus conversation
    history, produce the final streamed answer. This is the only agent
    that streams — every other agent runs to completion and returns a
    finished result, since their outputs need to be fully known before the
    response can be composed.
"""

from collections.abc import AsyncIterator

from app.ai.agents.base import AgentContext, AgentType, IAgent
from app.ai.providers.base import ChatTurn, ILLMProvider, StreamChunk


class ResponseAgent(IAgent):
    def __init__(self, llm_provider: ILLMProvider):
        self._llm_provider = llm_provider

    @property
    def agent_type(self) -> AgentType:
        return AgentType.RESPONSE

    async def run(self, context: AgentContext):
        raise NotImplementedError("ResponseAgent streams — use stream() instead of run()")

    async def stream(self, context: AgentContext, model: str = "gemini-3-flash") -> AsyncIterator[StreamChunk]:
        messages = list(context.history)

        if context.accumulated_context:
            findings = "\n\n".join(f"[{name}]\n{value}" for name, value in context.accumulated_context.items())
            messages.insert(0, ChatTurn(role="system", content=f"Gathered context for this response:\n{findings}"))

        messages.append(ChatTurn(role="user", content=context.user_message))

        async for chunk in self._llm_provider.stream_completion(messages=messages, model=model):
            yield chunk
