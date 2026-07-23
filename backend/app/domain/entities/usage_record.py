"""
domain/entities/usage_record.py

Why this file exists:
    Business record of one LLM call's cost/latency, captured per message
    exchange — powers token usage, cost estimation, and model usage
    breakdowns on the admin analytics dashboard.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

# Rough per-1K-token USD pricing for cost estimation DISPLAY purposes only —
# NOT used for billing. Update as providers change pricing.
_PRICING_PER_1K_TOKENS = {
    "gemini-3-flash": {"prompt": 0.00015, "completion": 0.0006},
    "mock": {"prompt": 0.0, "completion": 0.0},
}


@dataclass
class UsageRecord:
    user_id: UUID
    conversation_id: UUID
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def estimated_cost_usd(self) -> float:
        pricing = _PRICING_PER_1K_TOKENS.get(self.model, {"prompt": 0.0, "completion": 0.0})
        return (self.prompt_tokens / 1000) * pricing["prompt"] + (self.completion_tokens / 1000) * pricing["completion"]
