"""
application/use_cases/send_message.py

Why this file exists:
    This is the heart of the chat engine. It orchestrates, in order:
    1. Load conversation history (for context)
    2. Persist the user's message
    3. Stream the assistant's response from the LLM provider
    4. Persist the complete assistant message once streaming finishes
    5. Trigger title generation if this was the first exchange
    A router calling this doesn't need to know any of that — it just
    forwards the async generator to the client as SSE.

How it communicates with other modules:
    - Depends on IConversationRepository, IMessageRepository (interfaces)
    - Depends on ai/providers/base.ILLMProvider (interface)
    - Depends on application/services/title_generation_service
    - Raises ConversationNotFoundError / ConversationAccessDeniedError
"""

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from uuid import UUID

import time

from app.ai.memory.long_term import LongTermMemoryManager
from app.ai.memory.short_term import ShortTermMemoryManager
from app.ai.providers.base import ChatTurn, ILLMProvider
from app.application.services.title_generation_service import TitleGenerationService
from app.application.use_cases.search_documents import SearchDocumentsUseCase
from app.domain.entities.message import Message, MessageRole
from app.domain.exceptions.chat_exceptions import (
    ConversationAccessDeniedError,
    ConversationNotFoundError,
)
from app.domain.repositories.chat_repository import IConversationRepository, IMessageRepository

logger = logging.getLogger(__name__)


@dataclass
class StreamedToken:
    """What the router streams to the client as an SSE event."""

    text: str
    done: bool = False
    message_id: str | None = None


class SendMessageUseCase:
    def __init__(
        self,
        conversation_repository: IConversationRepository,
        message_repository: IMessageRepository,
        llm_provider: ILLMProvider,
        title_service: TitleGenerationService,
        short_term_memory: ShortTermMemoryManager,
        long_term_memory: LongTermMemoryManager,
        search_documents: SearchDocumentsUseCase,
        usage_repository=None,
    ):
        self._conversation_repository = conversation_repository
        self._message_repository = message_repository
        self._llm_provider = llm_provider
        self._title_service = title_service
        self._short_term_memory = short_term_memory
        self._long_term_memory = long_term_memory
        self._search_documents = search_documents
        self._usage_repository = usage_repository

    async def execute(
        self,
        user_id: UUID,
        conversation_id: UUID,
        content: str,
        model: str = "gemini-3-flash",
        document_ids: list[UUID] | None = None,
    ) -> AsyncIterator[StreamedToken]:
        conversation = await self._conversation_repository.get_by_id(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError(conversation_id)
        if conversation.user_id != user_id:
            raise ConversationAccessDeniedError()

        is_first_exchange = conversation.needs_title_generation()

        # Load history BEFORE saving the new user message, then append it
        # in-memory for the provider call — avoids a second DB round trip.
        history = await self._message_repository.list_by_conversation(conversation_id, limit=50)
        user_message = Message(conversation_id=conversation_id, role=MessageRole.USER, content=content)
        await self._message_repository.create(user_message)

        # Short-term memory: token-budgeted context instead of raw history —
        # summarizes older turns once the conversation grows past the budget.
        provider_messages = await self._short_term_memory.build_context(history)
        provider_messages.append(ChatTurn(role="user", content=content))

        # Long-term memory: inject relevant durable facts/preferences about
        # this user, retrieved by semantic similarity to the current message.
        relevant_memories = await self._long_term_memory.recall(user_id, query=content, top_k=5)
        if relevant_memories:
            memory_text = "\n".join(f"- {m.content}" for m in relevant_memories)
            provider_messages.insert(0, ChatTurn(role="system", content=f"Known about this user:\n{memory_text}"))

        # RAG: if the user attached documents to this conversation, retrieve
        # relevant chunks and inject them WITH citations, so the model can
        # (and should be instructed via the system prompt, in a full build,
        # to) attribute claims back to a specific source document.
        if document_ids:
            retrieved_chunks = await self._search_documents.execute(user_id, query=content, document_ids=document_ids)
            if retrieved_chunks:
                cited_context = "\n\n".join(
                    f"[Source: {c.document_filename}, chunk {c.chunk_index}]\n{c.content}" for c in retrieved_chunks
                )
                provider_messages.insert(
                    0,
                    ChatTurn(
                        role="system",
                        content=(
                            "Relevant excerpts from the user's documents. Cite the source "
                            f"filename when using this information:\n\n{cited_context}"
                        ),
                    ),
                )

        assistant_text_parts: list[str] = []
        prompt_tokens = completion_tokens = None
        stream_start = time.monotonic()

        async for chunk in self._llm_provider.stream_completion(messages=provider_messages, model=model):
            if chunk.text:
                assistant_text_parts.append(chunk.text)
                yield StreamedToken(text=chunk.text)
            if chunk.is_final:
                prompt_tokens = chunk.prompt_tokens
                completion_tokens = chunk.completion_tokens

        assistant_message = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content="".join(assistant_text_parts),
            model_provider=self._llm_provider.provider_name,
            model_name=model,
            token_count=completion_tokens,
            parent_message_id=user_message.id,
        )
        saved_assistant_message = await self._message_repository.create(assistant_message)
        latency_ms = int((time.monotonic() - stream_start) * 1000)

        if self._usage_repository is not None:
            from app.domain.entities.usage_record import UsageRecord

            await self._usage_repository.create(
                UsageRecord(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    provider=self._llm_provider.provider_name,
                    model=model,
                    prompt_tokens=prompt_tokens or 0,
                    completion_tokens=completion_tokens or 0,
                    latency_ms=latency_ms,
                )
            )

        yield StreamedToken(text="", done=True, message_id=str(saved_assistant_message.id))

        if is_first_exchange:
            try:
                title = await self._title_service.generate(content)
                conversation.title = title
                await self._conversation_repository.update(conversation)
            except Exception:
                logger.exception("Title generation failed for conversation %s", conversation_id)

        logger.info(
            "Message exchange complete: conversation=%s prompt_tokens=%s completion_tokens=%s",
            conversation_id,
            prompt_tokens,
            completion_tokens,
        )
