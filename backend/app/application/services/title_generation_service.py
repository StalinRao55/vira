"""
application/services/title_generation_service.py

Why this file exists:
    "Automatic conversation title generation" (spec) is a small, reusable
    capability that itself calls the AI layer — it belongs in
    application/services rather than being copy-pasted logic inside
    SendMessageUseCase. It depends on ILLMProvider (interface), not any
    concrete provider.

How it communicates with other modules:
    - Depends on ai/providers/base.ILLMProvider
    - Called by application/use_cases/send_message.py after the first
      exchange in a conversation completes
"""

from app.ai.providers.base import ChatTurn, ILLMProvider

_TITLE_PROMPT = (
    "Summarize the following user message as a short chat title, "
    "max 6 words, no punctuation, no quotes:\n\n{message}"
)


class TitleGenerationService:
    def __init__(self, llm_provider: ILLMProvider):
        self._llm_provider = llm_provider

    async def generate(self, first_user_message: str) -> str:
        """Runs a non-streamed, cheap completion to produce a short title.
        Falls back to a truncated version of the message on any failure —
        title generation must never break the chat flow."""
        try:
            prompt = _TITLE_PROMPT.format(message=first_user_message[:500])
            chunks = [
                chunk.text
                async for chunk in self._llm_provider.stream_completion(
                    messages=[ChatTurn(role="user", content=prompt)],
                    model="gemini-3-flash",
                    temperature=0.3,
                )
            ]
            title = "".join(chunks).strip().strip('"')
            return title[:80] if title else self._fallback(first_user_message)
        except Exception:
            return self._fallback(first_user_message)

    @staticmethod
    def _fallback(message: str) -> str:
        return (message[:47] + "...") if len(message) > 50 else message
