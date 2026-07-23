"""
tests/unit/ai/test_short_term_memory.py

Why this file exists:
    Verifies short-term memory does the right thing in both regimes: pass
    history through untouched when it fits the budget, and compress older
    messages into a summary once it doesn't — while always keeping the
    most recent messages verbatim.
"""

from uuid import uuid4

import pytest

from app.ai.memory.short_term import ShortTermMemoryManager
from app.ai.providers.mock_provider import MockProvider
from app.domain.entities.message import Message, MessageRole


def _make_message(role: MessageRole, content: str) -> Message:
    return Message(conversation_id=uuid4(), role=role, content=content)


@pytest.mark.asyncio
async def test_short_history_passes_through_unchanged():
    manager = ShortTermMemoryManager(MockProvider(), max_context_tokens=6000, keep_recent=10)
    history = [_make_message(MessageRole.USER, "Hi"), _make_message(MessageRole.ASSISTANT, "Hello!")]

    context = await manager.build_context(history)

    assert len(context) == 2
    assert context[0].content == "Hi"
    assert context[1].content == "Hello!"


@pytest.mark.asyncio
async def test_long_history_gets_compressed_with_recent_kept_verbatim():
    manager = ShortTermMemoryManager(
        MockProvider(canned_response="Summary of earlier discussion"),
        max_context_tokens=50,  # deliberately tiny to force compression
        keep_recent=2,
    )
    # 10 messages, each long enough to exceed the tiny token budget
    history = [_make_message(MessageRole.USER, f"This is message number {i} with some extra padding text") for i in range(10)]

    context = await manager.build_context(history)

    # First turn should be the summary (injected as a system message)
    assert context[0].role == "system"
    assert "summary" in context[0].content.lower()
    # Last two messages should be the original, uncompressed recent ones
    assert context[-1].content == history[-1].content
    assert context[-2].content == history[-2].content
    # Total length should be far less than the full raw history
    assert len(context) == 1 + 2  # 1 summary turn + keep_recent
