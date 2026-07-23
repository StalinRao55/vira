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

from collections.abc import AsyncIterator

import httpx

from app.ai.providers.base import ChatTurn, ILLMProvider, StreamChunk

_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


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
        model: str = "gemini-3-flash",
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

        completion_text_len = 0
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, params=params, json=payload) as response:
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
                        completion_text_len += len(text)
                        yield StreamChunk(text=text)

                    usage = data.get("usageMetadata")
                    if usage:
                        yield StreamChunk(
                            text="",
                            is_final=True,
                            prompt_tokens=usage.get("promptTokenCount"),
                            completion_tokens=usage.get("candidatesTokenCount"),
                        )
