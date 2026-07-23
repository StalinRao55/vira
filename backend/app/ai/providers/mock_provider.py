"""
ai/providers/mock_provider.py

Why this file exists:
    Lets us build and test the entire chat engine (streaming, persistence,
    title generation) without calling a real API or spending quota. Also
    useful in CI, where you don't want tests depending on network access or
    secrets.

How it communicates with other modules:
    - Implements ai/providers/base.ILLMProvider
    - Selected by ai/providers/factory.py when settings.default_provider
      == "mock", or used directly in tests
"""

import asyncio
from collections.abc import AsyncIterator

from app.ai.providers.base import ChatTurn, ILLMProvider, StreamChunk


class MockProvider(ILLMProvider):
    """Echoes a canned response, word by word, simulating streaming
    latency. Deterministic and offline — ideal for tests."""

    def __init__(self, canned_response: str | None = None):
        self._canned_response = canned_response

    @property
    def provider_name(self) -> str:
        return "mock"

    async def stream_completion(
        self,
        messages: list[ChatTurn],
        model: str = "mock-model",
        temperature: float = 0.7,
    ) -> AsyncIterator[StreamChunk]:
        last_user_message = next((m.content for m in reversed(messages) if m.role == "user"), "")
        response = self._canned_response or f"This is a mock response to: {last_user_message[:50]}"

        words = response.split(" ")
        for i, word in enumerate(words):
            await asyncio.sleep(0)  # yield control, simulate async I/O without real delay
            yield StreamChunk(text=word + (" " if i < len(words) - 1 else ""))

        yield StreamChunk(
            text="",
            is_final=True,
            prompt_tokens=sum(len(m.content.split()) for m in messages),
            completion_tokens=len(words),
        )
