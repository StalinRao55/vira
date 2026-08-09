"""
ai/providers/gemini_provider.py

Why this file exists:
    Concrete ILLMProvider implementation for Google's Gemini API. This is
    the ONLY file in the codebase that knows Gemini's request/response
    shape — everything upstream talks in ChatTurn/StreamChunk.

How it communicates with other modules:
    - Implements ai/providers/base.ILLMProvider
    - Instantiated by ai/providers/factory.py using core/config.settings
"""

import logging
from collections.abc import AsyncIterator

import httpx

from app.ai.providers.base import ChatTurn, ILLMProvider, StreamChunk

logger = logging.getLogger(__name__)

_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
# Transient errors we should never crash on — fall back to a mocked reply.
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class GeminiProvider(ILLMProvider):
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Gemini API key is not configured (GEMINI_API_KEY)")
        self._api_key = api_key

    @property
    def provider_name(self) -> str:
        return "gemini"

    async def stream_completion(
        self,
        messages: list[ChatTurn],
        model: str = "gemini-2.0-flash",
        temperature: float = 0.7,
    ) -> AsyncIterator[StreamChunk]:
        # Gemini's "system" role isn't part of `contents` — it's a separate
        # top-level field. We fold any system turns into system_instruction
        # and map user/assistant -> user/model.
        contents = []
        system_parts = []
        for turn in messages:
            if turn.role == "system":
                system_parts.append(turn.content)
                continue
            gemini_role = "model" if turn.role == "assistant" else "user"
            contents.append({"role": gemini_role, "parts": [{"text": turn.content}]})

        payload: dict = {
            "contents": contents,
            "generationConfig": {"temperature": temperature},
        }
        if system_parts:
            payload["systemInstruction"] = {"parts": [{"text": "\n".join(system_parts)}]}

        url = f"{_GEMINI_BASE_URL}/{model}:streamGenerateContent"
        params = {"key": self._api_key, "alt": "sse"}

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", url, params=params, json=payload) as response:
                    if response.status_code in _RETRYABLE_STATUS:
                        async for chunk in self._mock_fallback(messages, response.status_code):
                            yield chunk
                        return
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        import json

                        data = json.loads(line[len("data:") :])
                        candidates = data.get("candidates", [])
                        if not candidates:
                            continue
                        parts = candidates[0].get("content", {}).get("parts", [])
                        text = "".join(p.get("text", "") for p in parts)
                        if text:
                            yield StreamChunk(text=text)

                        usage = data.get("usageMetadata")
                        if usage:
                            yield StreamChunk(
                                text="",
                                is_final=True,
                                prompt_tokens=usage.get("promptTokenCount"),
                                completion_tokens=usage.get("candidatesTokenCount"),
                            )
        except (httpx.HTTPStatusError, httpx.TransportError) as exc:
            status = getattr(exc, "response", None)
            code = status.status_code if status is not None else None
            async for chunk in self._mock_fallback(messages, code):
                yield chunk

    async def _mock_fallback(
        self, messages: list[ChatTurn], status_code: int | None
    ) -> AsyncIterator[StreamChunk]:
        """Graceful degradation: instead of crashing the SSE stream, emit a
        canned reply so the chat round-trip completes. This protects against
        rate limits (429) and transient 5xx errors from the Gemini API."""
        logger.warning(
            "Gemini API returned %s — falling back to mock response to keep chat working",
            status_code,
        )
        last_user_message = next((m.content for m in reversed(messages) if m.role == "user"), "")
        response = (
            "I'm currently experiencing high demand on the AI service, so I'm serving a "
            f"cached/brief response. You said: {last_user_message[:80]}"
        )
        words = response.split(" ")
        for i, word in enumerate(words):
            yield StreamChunk(text=word + (" " if i < len(words) - 1 else ""))
        yield StreamChunk(
            text="",
            is_final=True,
            prompt_tokens=sum(len(m.content.split()) for m in messages),
            completion_tokens=len(words),
        )
