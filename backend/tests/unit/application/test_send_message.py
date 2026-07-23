"""
tests/unit/application/test_send_message.py

Why this file exists:
    Verifies the full chat engine orchestration (history load, user message
    save, streamed assistant response, assistant message save, auto-title
    generation) without a real database or real LLM API — using in-memory
    fakes and MockProvider. This is the payoff of the interface-based
    design: the whole chat engine is testable in milliseconds.
"""

from uuid import uuid4

import pytest

from app.ai.embeddings.mock_embedding_provider import MockEmbeddingProvider
from app.ai.memory.long_term import LongTermMemoryManager
from app.ai.memory.short_term import ShortTermMemoryManager
from app.ai.providers.mock_provider import MockProvider
from app.ai.rag.rag_engine import RAGEngine
from app.application.services.title_generation_service import TitleGenerationService
from app.application.use_cases.search_documents import SearchDocumentsUseCase
from app.application.use_cases.send_message import SendMessageUseCase
from app.domain.entities.conversation import Conversation
from app.domain.entities.document import Document, DocumentChunk
from app.domain.entities.memory import Memory
from app.domain.entities.message import Message
from app.domain.repositories.chat_repository import IConversationRepository, IMessageRepository
from app.domain.repositories.document_repository import IDocumentChunkRepository, IDocumentRepository
from app.domain.repositories.memory_repository import IMemoryRepository
from app.infrastructure.vector_store.faiss_vector_store import FaissVectorStore


class InMemoryConversationRepository(IConversationRepository):
    def __init__(self):
        self._data: dict = {}

    async def get_by_id(self, conversation_id):
        return self._data.get(conversation_id)

    async def list_by_user(self, user_id, include_archived=False, limit=50, offset=0):
        return [c for c in self._data.values() if c.user_id == user_id]

    async def search_by_title(self, user_id, query):
        return [c for c in self._data.values() if c.user_id == user_id and query.lower() in c.title.lower()]

    async def create(self, conversation):
        self._data[conversation.id] = conversation
        return conversation

    async def update(self, conversation):
        self._data[conversation.id] = conversation
        return conversation

    async def delete(self, conversation_id):
        self._data.pop(conversation_id, None)


class InMemoryMessageRepository(IMessageRepository):
    def __init__(self):
        self._data: list[Message] = []

    async def get_by_id(self, message_id):
        return next((m for m in self._data if m.id == message_id), None)

    async def list_by_conversation(self, conversation_id, limit=50, before=None):
        return [m for m in self._data if m.conversation_id == conversation_id][:limit]

    async def create(self, message):
        self._data.append(message)
        return message


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


class InMemoryDocumentRepository(IDocumentRepository):
    def __init__(self):
        self._data: dict = {}

    async def get_by_id(self, document_id):
        return self._data.get(document_id)

    async def list_by_user(self, user_id):
        return [d for d in self._data.values() if d.user_id == user_id]

    async def create(self, document: Document):
        self._data[document.id] = document
        return document

    async def update_status(self, document_id, status):
        if document_id in self._data:
            self._data[document_id].status = status

    async def delete(self, document_id):
        self._data.pop(document_id, None)


class InMemoryDocumentChunkRepository(IDocumentChunkRepository):
    def __init__(self):
        self._data: list[DocumentChunk] = []

    async def create_many(self, chunks):
        self._data.extend(chunks)
        return chunks

    async def list_by_document(self, document_id):
        return [c for c in self._data if c.document_id == document_id]

    async def get_by_ids(self, chunk_ids):
        return [c for c in self._data if c.id in chunk_ids]

    async def delete_by_document(self, document_id):
        self._data = [c for c in self._data if c.document_id != document_id]


def _build_use_case(conversation_repo, message_repo, provider, title_service):
    """Wires a fully-functional SendMessageUseCase with a fresh, isolated
    memory + RAG stack — a FAISS store per test avoids cross-test vector bleed."""
    short_term_memory = ShortTermMemoryManager(provider, max_context_tokens=6000, keep_recent=10)
    long_term_memory = LongTermMemoryManager(
        memory_repository=InMemoryMemoryRepository(),
        vector_store=FaissVectorStore(dimensions=32),
        embedding_provider=MockEmbeddingProvider(),
    )
    rag_engine = RAGEngine(embedding_provider=MockEmbeddingProvider(), vector_store=FaissVectorStore(dimensions=32))
    search_documents = SearchDocumentsUseCase(
        rag_engine=rag_engine,
        document_repository=InMemoryDocumentRepository(),
        chunk_repository=InMemoryDocumentChunkRepository(),
    )
    return SendMessageUseCase(
        conversation_repo,
        message_repo,
        provider,
        title_service,
        short_term_memory,
        long_term_memory,
        search_documents,
    )


@pytest.mark.asyncio
async def test_send_message_streams_and_persists_and_titles():
    conversation_repo = InMemoryConversationRepository()
    message_repo = InMemoryMessageRepository()
    provider = MockProvider(canned_response="Hello there, how can I help?")
    title_service = TitleGenerationService(MockProvider(canned_response="Greeting exchange"))

    user_id = uuid4()
    conversation = await conversation_repo.create(Conversation(user_id=user_id))

    use_case = _build_use_case(conversation_repo, message_repo, provider, title_service)

    collected_text = ""
    saw_done = False
    async for token in use_case.execute(user_id=user_id, conversation_id=conversation.id, content="Hi!"):
        collected_text += token.text
        if token.done:
            saw_done = True
            assert token.message_id is not None

    assert saw_done
    assert collected_text.strip() == "Hello there, how can I help?"

    # Both user and assistant messages were persisted
    stored = await message_repo.list_by_conversation(conversation.id)
    assert len(stored) == 2
    assert stored[0].role.value == "user"
    assert stored[1].role.value == "assistant"
    assert stored[1].parent_message_id == stored[0].id

    # Title was auto-generated since this was the first exchange
    updated_conversation = await conversation_repo.get_by_id(conversation.id)
    assert updated_conversation.title == "Greeting exchange"


@pytest.mark.asyncio
async def test_second_message_does_not_regenerate_title():
    conversation_repo = InMemoryConversationRepository()
    message_repo = InMemoryMessageRepository()
    provider = MockProvider(canned_response="Sure thing.")
    title_service = TitleGenerationService(MockProvider(canned_response="Should not be used"))

    user_id = uuid4()
    conversation = Conversation(user_id=user_id, title="Already titled")
    await conversation_repo.create(conversation)

    use_case = _build_use_case(conversation_repo, message_repo, provider, title_service)

    async for _ in use_case.execute(user_id=user_id, conversation_id=conversation.id, content="Follow up"):
        pass

    updated_conversation = await conversation_repo.get_by_id(conversation.id)
    assert updated_conversation.title == "Already titled"
