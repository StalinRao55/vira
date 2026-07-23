"""
ai/memory/short_term.py

Why this file exists:
    Manages what fits in the model's context window for a single request.
    Naive "send the whole history" breaks down once a conversation gets
    long — cost grows unbounded and eventually exceeds the model's context
    limit. This class enforces a token budget: keep the most recent N
    messages verbatim, and if older messages exist beyond that, compress
    them into a single summary message via the LLM provider.

How it communicates with other modules:
    - Depends on ai/providers/base.ILLMProvider (interface) to generate
      summaries
    - Consumed by application/use_cases/send_message.py, which calls
      build_context() instead of using raw history directly
"""

import logging

from app.ai.providers.base import ChatTurn, ILLMProvider
from app.domain.entities.message import Message

logger = logging.getLogger(__name__)

# Rough heuristic: ~4 characters per token for English text. Good enough for
# budgeting decisions without pulling in a full tokenizer dependency; swap
# for a real tokenizer (e.g. tiktoken-equivalent for the active model) if
# precise token accounting becomes important for cost tracking.
_CHARS_PER_TOKEN_ESTIMATE = 4

_SUMMARY_PROMPT = (
    "Summarize the following conversation history concisely, preserving "
    "any facts, decisions, or preferences that would matter for answering "
    "future questions. Write it as a neutral third-person summary:\n\n{history}"
)


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // _CHARS_PER_TOKEN_ESTIMATE)


class ShortTermMemoryManager:
    def __init__(self, llm_provider: ILLMProvider, max_context_tokens: int = 6000, keep_recent: int = 10):
        self._llm_provider = llm_provider
        self._max_context_tokens = max_context_tokens
        self._keep_recent = keep_recent

    async def build_context(self, history: list[Message]) -> list[ChatTurn]:
        """Returns a token-budgeted list of ChatTurns ready to send to the
        LLM provider: either the full history verbatim (if it fits), or a
        summary of the older portion followed by the most recent messages
        verbatim."""
        total_tokens = sum(estimate_tokens(m.content) for m in history)

        if total_tokens <= self._max_context_tokens or len(history) <= self._keep_recent:
            return [ChatTurn(role=m.role.value, content=m.content) for m in history]

        older = history[: -self._keep_recent]
        recent = history[-self._keep_recent :]

        summary_text = await self._summarize(older)
        logger.info("Compressed %d older messages into a summary (%d tokens saved estimate)", len(older), total_tokens)

        context = [ChatTurn(role="system", content=f"Earlier conversation summary: {summary_text}")]
        context.extend(ChatTurn(role=m.role.value, content=m.content) for m in recent)
        return context

    async def _summarize(self, messages: list[Message]) -> str:
        transcript = "\n".join(f"{m.role.value}: {m.content}" for m in messages)
        prompt = _SUMMARY_PROMPT.format(history=transcript[:8000])  # cap input to the summarizer itself
        try:
            chunks = [
                chunk.text
                async for chunk in self._llm_provider.stream_completion(
                    messages=[ChatTurn(role="user", content=prompt)], model="gemini-3-flash", temperature=0.2
                )
            ]
            return "".join(chunks).strip()
        except Exception:
            logger.exception("Summarization failed; falling back to truncated transcript")
            return transcript[:1000]
