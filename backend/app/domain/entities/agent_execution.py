"""
domain/entities/agent_execution.py

Why this file exists:
    Business record of one agent's execution within a pipeline run —
    powers "Agent execution history" from the spec's persistence
    requirements and the future admin analytics dashboard (Phase 11).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass
class AgentExecution:
    message_id: UUID
    agent_type: str
    input_summary: str
    output_summary: str
    status: str  # "success" | "failed"
    duration_ms: int
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
