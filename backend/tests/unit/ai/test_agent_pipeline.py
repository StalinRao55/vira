"""
tests/unit/ai/test_agent_pipeline.py

Why this file exists:
    Verifies the coordinator correctly runs planner -> gathering steps ->
    response, entirely offline. Uses MockProvider configured to return a
    JSON plan for the planning call and a normal answer for the response
    call — proving the dual-purpose LLM usage (planning JSON vs response
    text) is wired correctly.
"""

from uuid import uuid4

import pytest

from app.ai.agents.base import AgentContext
from app.ai.agents.coordinator import CoordinatorAgent
from app.ai.agents.memory_agent import MemoryAgent
from app.ai.agents.planner import PlannerAgent
from app.ai.agents.research import ResearchAgent
from app.ai.agents.response_agent import ResponseAgent
from app.ai.agents.tool_agent import ToolAgent
from app.ai.embeddings.mock_embedding_provider import MockEmbeddingProvider
from app.ai.memory.long_term import LongTermMemoryManager
from app.ai.providers.mock_provider import MockProvider
from app.ai.tools.stub_executor import StubToolExecutor
from app.domain.entities.memory import Memory
from app.domain.repositories.memory_repository import IMemoryRepository
from app.infrastructure.vector_store.faiss_vector_store import FaissVectorStore


class InMemoryMemoryRepository(IMemoryRepository):
    def __init__(self):
        self._data: dict = {}

    async def get_by_id(self, memory_id):
        return self._data.get(memory_id)

    async def list_by_user(self, user_id, limit=100):
        return [m for m in self._data.values() if m.user_id == user_id][:limit]

    async def get_by_ids(self, memory_ids):
        return [self._data[mid] for mid in memory_ids if mid in self._data]

    async def create(self, memory: Memory):
        self._data[memory.id] = memory
        return memory

    async def touch_last_accessed(self, memory_id):
        pass

    async def delete(self, memory_id):
        self._data.pop(memory_id, None)


@pytest.mark.asyncio
async def test_coordinator_runs_plan_then_streams_response():
    # Planner call returns JSON naming "memory" as the only needed step;
    # response call returns the final canned answer. Real MockProvider
    # ignores the distinction (always echoes canned_response), so we give
    # it JSON that both the planner parser AND a plausible response accept —
    # here we use a provider that always returns valid JSON for planning.
    planner_provider = MockProvider(canned_response='["memory"]')
    response_provider = MockProvider(canned_response="Here is your answer based on what I know about you.")

    long_term_memory = LongTermMemoryManager(
        memory_repository=InMemoryMemoryRepository(),
        vector_store=FaissVectorStore(dimensions=32),
        embedding_provider=MockEmbeddingProvider(),
    )
    user_id = uuid4()
    await long_term_memory.remember(user_id, "User likes concise answers")

    tool_executor = StubToolExecutor()

    coordinator = CoordinatorAgent(
        planner=PlannerAgent(planner_provider),
        memory_agent=MemoryAgent(long_term_memory),
        research_agent=ResearchAgent(tool_executor),
        tool_agent=ToolAgent(tool_executor),
        response_agent=ResponseAgent(response_provider),
    )

    context = AgentContext(user_id=user_id, conversation_id=uuid4(), user_message="concise answers")

    agent_results = []
    response_text = ""
    async for result, chunk in coordinator.run_pipeline(context):
        if result is not None:
            agent_results.append(result)
        if chunk is not None:
            response_text += chunk.text

    agent_types = [r.agent_type.value for r in agent_results]
    assert "planner" in agent_types
    assert "memory" in agent_types
    assert response_text.strip() == "Here is your answer based on what I know about you."
    assert context.accumulated_context.get("memory") is not None


@pytest.mark.asyncio
async def test_planner_falls_back_to_empty_plan_on_malformed_json():
    planner_provider = MockProvider(canned_response="not valid json at all")
    from app.ai.agents.planner import PlannerAgent

    planner = PlannerAgent(planner_provider)
    context = AgentContext(user_id=uuid4(), conversation_id=uuid4(), user_message="hello")

    result = await planner.run(context)

    assert context.plan == []
    assert result.success is True  # malformed JSON is handled gracefully, not a hard failure
