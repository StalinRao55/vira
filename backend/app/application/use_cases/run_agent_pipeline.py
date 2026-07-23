"""
application/use_cases/run_agent_pipeline.py

Why this file exists:
    The agent-mode counterpart to SendMessageUseCase: instead of calling
    the LLM directly, routes through CoordinatorAgent so complex questions
    get planning + memory/research/tool gathering before the final answer.
    Persists both chat messages (same as SendMessageUseCase) AND an
    AgentExecution row per pipeline step — this is what populates "Agent
    execution history" for the admin dashboard.
"""

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from uuid import UUID

from app.ai.agents.base import AgentContext
from app.ai.agents.coordinator import CoordinatorAgent
from app.domain.entities.agent_execution import AgentExecution
from app.domain.entities.message import Message, MessageRole
from app.domain.exceptions.chat_exceptions import ConversationAccessDeniedError, ConversationNotFoundError
from app.domain.repositories.agent_execution_repository import IAgentExecutionRepository
from app.domain.repositories.chat_repository import IConversationRepository, IMessageRepository

logger = logging.getLogger(__name__)


@dataclass
class AgentStreamEvent:
    text: str = ""
    done: bool = False
    message_id: str | None = None
    agent_step: str | None = None  # set for planning/gathering step events, None for response tokens


class RunAgentPipelineUseCase:
    def __init__(
        self,
        conversation_repository: IConversationRepository,
        message_repository: IMessageRepository,
        agent_execution_repository: IAgentExecutionRepository,
        coordinator: CoordinatorAgent,
    ):
        self._conversation_repository = conversation_repository
        self._message_repository = message_repository
        self._agent_execution_repository = agent_execution_repository
        self._coordinator = coordinator

    async def execute(
        self, user_id: UUID, conversation_id: UUID, content: str, model: str = "gemini-3-flash"
    ) -> AsyncIterator[AgentStreamEvent]:
        conversation = await self._conversation_repository.get_by_id(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError(conversation_id)
        if conversation.user_id != user_id:
            raise ConversationAccessDeniedError()

        history = await self._message_repository.list_by_conversation(conversation_id, limit=50)
        user_message = Message(conversation_id=conversation_id, role=MessageRole.USER, content=content)
        await self._message_repository.create(user_message)

        from app.ai.providers.base import ChatTurn

        context = AgentContext(
            user_id=user_id,
            conversation_id=conversation_id,
            user_message=content,
            history=[ChatTurn(role=m.role.value, content=m.content) for m in history],
        )

        assistant_parts: list[str] = []

        async for agent_result, chunk in self._coordinator.run_pipeline(context, model=model):
            if agent_result is not None:
                execution = AgentExecution(
                    message_id=user_message.id,
                    agent_type=agent_result.agent_type.value,
                    input_summary=content[:500],
                    output_summary=agent_result.output[:1000],
                    status="success" if agent_result.success else "failed",
                    duration_ms=agent_result.metadata.get("duration_ms", 0),
                )
                await self._agent_execution_repository.create(execution)
                yield AgentStreamEvent(agent_step=agent_result.agent_type.value)
                continue

            if chunk is not None and chunk.text:
                assistant_parts.append(chunk.text)
                yield AgentStreamEvent(text=chunk.text)

        assistant_message = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content="".join(assistant_parts),
            model_provider="agent_pipeline",
            model_name=model,
            parent_message_id=user_message.id,
        )
        saved = await self._message_repository.create(assistant_message)
        yield AgentStreamEvent(done=True, message_id=str(saved.id))
