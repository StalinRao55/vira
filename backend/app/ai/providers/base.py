"""
ai/providers/base.py

Why this file exists:
    Defines the CONTRACT every model provider must satisfy. The
    application layer (SendMessageUseCase) depends only on this interface,
    never on GeminiProvider or OpenAIProvider directly. Adding a new
    provider means writing one class here and registering it in
    factory.py — zero changes to chat logic.

How it communicates with other modules:
    - Implemented by gemini_provider.py, mock_provider.py (and future
      openai_provider.py, anthropic_provider.py, ...)
    - Selected by ai/providers/factory.py based on config
    - Consumed by application/use_cases/send_message.py
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass
class ChatTurn:
    """One turn of conversation history sent to the provider. Kept
    provider-agnostic — each concrete provider translates this into its own
    wire format (e.g. Gemini's `contents` list)."""

    role: str  # "user" | "assistant" | "system"
    content: str


@dataclass
class StreamChunk:
    """A single piece of a streamed response. `is_final` carries usage
    stats once the stream completes, so callers don't need a second call to
    find out token counts."""

    text: str
    is_final: bool = False
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class ILLMProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    def stream_completion(
        self,
        messages: list[ChatTurn],
        model: str,
        temperature: float = 0.7,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a completion given conversation history. Implementations
        must yield StreamChunk objects and set is_final=True on the last
        one, ideally with token counts for the analytics/usage tables."""
        ...
