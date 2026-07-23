"""
api/v1/dependencies.py

Why this file exists:
    This is the dependency-injection seam: it constructs concrete
    implementations (PostgresUserRepository, use cases) and hands them to
    route handlers. Routers never instantiate a repository or use case
    themselves — they declare a dependency and FastAPI injects it. This is
    also where request-level authentication (get_current_user) lives, so
    any route can protect itself with a single Depends().

How it communicates with other modules:
    - Builds infrastructure/database/repositories/postgres_user_repository
    - Builds application/use_cases/*
    - Used by api/v1/routers/auth.py and (in later phases) every other
      protected router
"""

from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings.base import IEmbeddingProvider
from app.ai.embeddings.factory import get_embedding_provider
from app.ai.memory.long_term import LongTermMemoryManager
from app.ai.memory.short_term import ShortTermMemoryManager
from app.ai.providers.base import ILLMProvider
from app.ai.providers.factory import get_llm_provider
from app.ai.rag.rag_engine import RAGEngine
from app.application.services.title_generation_service import TitleGenerationService
from app.application.use_cases.create_conversation import CreateConversationUseCase
from app.application.use_cases.list_conversations import (
    ListConversationsUseCase,
    SearchConversationsUseCase,
)
from app.application.use_cases.login_user import LoginUserUseCase
from app.application.use_cases.oauth_user import OAuthUserUseCase
from app.application.use_cases.manage_documents import DeleteDocumentUseCase, ListDocumentsUseCase
from app.application.use_cases.manage_memory import (
    CreateMemoryUseCase,
    DeleteMemoryUseCase,
    ListMemoriesUseCase,
)
from app.application.use_cases.refresh_token import RefreshTokenUseCase
from app.application.use_cases.register_user import RegisterUserUseCase
from app.application.use_cases.request_password_reset import RequestPasswordResetUseCase
from app.application.use_cases.reset_password import ResetPasswordUseCase
from app.application.use_cases.search_documents import SearchDocumentsUseCase
from app.application.use_cases.send_message import SendMessageUseCase
from app.application.use_cases.update_conversation import (
    DeleteConversationUseCase,
    UpdateConversationUseCase,
)
from app.application.use_cases.upload_document import UploadDocumentUseCase
from app.core.security import TokenType, decode_token
from app.domain.entities.user import User
from app.infrastructure.database.base import get_session
from app.infrastructure.database.repositories.postgres_chat_repository import (
    PostgresConversationRepository,
    PostgresMessageRepository,
)
from app.infrastructure.database.repositories.postgres_document_repository import (
    PostgresDocumentChunkRepository,
    PostgresDocumentRepository,
)
from app.infrastructure.database.repositories.postgres_memory_repository import PostgresMemoryRepository
from app.infrastructure.database.repositories.postgres_password_reset_repository import PostgresPasswordResetRepository
from app.infrastructure.database.repositories.postgres_usage_repository import PostgresUsageRepository
from app.infrastructure.database.repositories.postgres_user_repository import PostgresUserRepository
from app.infrastructure.storage.base import IFileStorage
from app.infrastructure.storage.factory import get_file_storage
from app.infrastructure.vector_store.base import IVectorStore
from app.infrastructure.vector_store.factory import get_vector_store

_bearer_scheme = HTTPBearer()


def get_user_repository(session: Annotated[AsyncSession, Depends(get_session)]) -> PostgresUserRepository:
    return PostgresUserRepository(session)


def get_register_use_case(
    repo: Annotated[PostgresUserRepository, Depends(get_user_repository)],
) -> RegisterUserUseCase:
    return RegisterUserUseCase(repo)


def get_login_use_case(
    repo: Annotated[PostgresUserRepository, Depends(get_user_repository)],
) -> LoginUserUseCase:
    return LoginUserUseCase(repo)


def get_oauth_use_case(
    repo: Annotated[PostgresUserRepository, Depends(get_user_repository)],
) -> OAuthUserUseCase:
    return OAuthUserUseCase(repo)


def get_password_reset_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PostgresPasswordResetRepository:
    return PostgresPasswordResetRepository(session)


def get_request_password_reset_use_case(
    user_repo: Annotated[PostgresUserRepository, Depends(get_user_repository)],
    reset_repo: Annotated[PostgresPasswordResetRepository, Depends(get_password_reset_repository)],
) -> RequestPasswordResetUseCase:
    return RequestPasswordResetUseCase(user_repo, reset_repo)


def get_reset_password_use_case(
    user_repo: Annotated[PostgresUserRepository, Depends(get_user_repository)],
    reset_repo: Annotated[PostgresPasswordResetRepository, Depends(get_password_reset_repository)],
) -> ResetPasswordUseCase:
    return ResetPasswordUseCase(user_repo, reset_repo)


def get_refresh_use_case(
    repo: Annotated[PostgresUserRepository, Depends(get_user_repository)],
) -> RefreshTokenUseCase:
    return RefreshTokenUseCase(repo)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer_scheme)],
    repo: Annotated[PostgresUserRepository, Depends(get_user_repository)],
) -> User:
    """Protects any route that depends on it. Decodes the access token from
    the Authorization header, loads the user, and raises 401 on any
    failure — invalid signature, expired token, or missing user."""
    try:
        user_id_str = decode_token(credentials.credentials, expected_type=TokenType.ACCESS)
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        ) from exc

    user = await repo.get_by_id(UUID(user_id_str))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def require_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """RBAC guard for admin-only routes (used by the analytics dashboard in
    Phase 11)."""
    if current_user.role.value != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


# --- Chat engine dependencies ---


def get_conversation_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PostgresConversationRepository:
    return PostgresConversationRepository(session)


def get_message_repository(session: Annotated[AsyncSession, Depends(get_session)]) -> PostgresMessageRepository:
    return PostgresMessageRepository(session)


def get_current_llm_provider() -> ILLMProvider:
    """Resolves the active provider from config. Swapping providers is a
    config change (see ai/providers/factory.py) — nothing here changes."""
    return get_llm_provider()


def get_title_generation_service(
    llm_provider: Annotated[ILLMProvider, Depends(get_current_llm_provider)],
) -> TitleGenerationService:
    return TitleGenerationService(llm_provider)


def get_create_conversation_use_case(
    repo: Annotated[PostgresConversationRepository, Depends(get_conversation_repository)],
) -> CreateConversationUseCase:
    return CreateConversationUseCase(repo)


def get_list_conversations_use_case(
    repo: Annotated[PostgresConversationRepository, Depends(get_conversation_repository)],
) -> ListConversationsUseCase:
    return ListConversationsUseCase(repo)


def get_search_conversations_use_case(
    repo: Annotated[PostgresConversationRepository, Depends(get_conversation_repository)],
) -> SearchConversationsUseCase:
    return SearchConversationsUseCase(repo)


def get_update_conversation_use_case(
    repo: Annotated[PostgresConversationRepository, Depends(get_conversation_repository)],
) -> UpdateConversationUseCase:
    return UpdateConversationUseCase(repo)


def get_delete_conversation_use_case(
    repo: Annotated[PostgresConversationRepository, Depends(get_conversation_repository)],
) -> DeleteConversationUseCase:
    return DeleteConversationUseCase(repo)


# --- Memory system dependencies ---


def get_memory_repository(session: Annotated[AsyncSession, Depends(get_session)]) -> PostgresMemoryRepository:
    return PostgresMemoryRepository(session)


def get_embedding_provider_dep() -> IEmbeddingProvider:
    return get_embedding_provider()


def get_vector_store_dep() -> IVectorStore:
    return get_vector_store()


def get_short_term_memory_manager(
    llm_provider: Annotated[ILLMProvider, Depends(get_current_llm_provider)],
) -> ShortTermMemoryManager:
    return ShortTermMemoryManager(llm_provider)


def get_long_term_memory_manager(
    memory_repo: Annotated[PostgresMemoryRepository, Depends(get_memory_repository)],
    vector_store: Annotated[IVectorStore, Depends(get_vector_store_dep)],
    embedding_provider: Annotated[IEmbeddingProvider, Depends(get_embedding_provider_dep)],
) -> LongTermMemoryManager:
    return LongTermMemoryManager(memory_repo, vector_store, embedding_provider)


def get_create_memory_use_case(
    long_term_memory: Annotated[LongTermMemoryManager, Depends(get_long_term_memory_manager)],
) -> CreateMemoryUseCase:
    return CreateMemoryUseCase(long_term_memory)


def get_list_memories_use_case(
    repo: Annotated[PostgresMemoryRepository, Depends(get_memory_repository)],
) -> ListMemoriesUseCase:
    return ListMemoriesUseCase(repo)


def get_delete_memory_use_case(
    repo: Annotated[PostgresMemoryRepository, Depends(get_memory_repository)],
) -> DeleteMemoryUseCase:
    return DeleteMemoryUseCase(repo)


# --- Document / RAG dependencies ---


def get_document_repository(session: Annotated[AsyncSession, Depends(get_session)]) -> PostgresDocumentRepository:
    return PostgresDocumentRepository(session)


def get_document_chunk_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PostgresDocumentChunkRepository:
    return PostgresDocumentChunkRepository(session)


def get_file_storage_dep() -> IFileStorage:
    return get_file_storage()


def get_rag_engine(
    embedding_provider: Annotated[IEmbeddingProvider, Depends(get_embedding_provider_dep)],
    vector_store: Annotated[IVectorStore, Depends(get_vector_store_dep)],
) -> RAGEngine:
    return RAGEngine(embedding_provider, vector_store)


def get_upload_document_use_case(
    document_repo: Annotated[PostgresDocumentRepository, Depends(get_document_repository)],
    chunk_repo: Annotated[PostgresDocumentChunkRepository, Depends(get_document_chunk_repository)],
    file_storage: Annotated[IFileStorage, Depends(get_file_storage_dep)],
    rag_engine: Annotated[RAGEngine, Depends(get_rag_engine)],
) -> UploadDocumentUseCase:
    return UploadDocumentUseCase(document_repo, chunk_repo, file_storage, rag_engine)


def get_list_documents_use_case(
    repo: Annotated[PostgresDocumentRepository, Depends(get_document_repository)],
) -> ListDocumentsUseCase:
    return ListDocumentsUseCase(repo)


def get_delete_document_use_case(
    document_repo: Annotated[PostgresDocumentRepository, Depends(get_document_repository)],
    chunk_repo: Annotated[PostgresDocumentChunkRepository, Depends(get_document_chunk_repository)],
    file_storage: Annotated[IFileStorage, Depends(get_file_storage_dep)],
    vector_store: Annotated[IVectorStore, Depends(get_vector_store_dep)],
) -> DeleteDocumentUseCase:
    return DeleteDocumentUseCase(document_repo, chunk_repo, file_storage, vector_store)


def get_search_documents_use_case(
    rag_engine: Annotated[RAGEngine, Depends(get_rag_engine)],
    document_repo: Annotated[PostgresDocumentRepository, Depends(get_document_repository)],
    chunk_repo: Annotated[PostgresDocumentChunkRepository, Depends(get_document_chunk_repository)],
) -> SearchDocumentsUseCase:
    return SearchDocumentsUseCase(rag_engine, document_repo, chunk_repo)


# --- Chat engine dependencies that need the memory system and RAG above ---


def get_usage_repository(session: Annotated[AsyncSession, Depends(get_session)]) -> PostgresUsageRepository:
    return PostgresUsageRepository(session)


def get_send_message_use_case(
    conversation_repo: Annotated[PostgresConversationRepository, Depends(get_conversation_repository)],
    message_repo: Annotated[PostgresMessageRepository, Depends(get_message_repository)],
    llm_provider: Annotated[ILLMProvider, Depends(get_current_llm_provider)],
    title_service: Annotated[TitleGenerationService, Depends(get_title_generation_service)],
    short_term_memory: Annotated[ShortTermMemoryManager, Depends(get_short_term_memory_manager)],
    long_term_memory: Annotated[LongTermMemoryManager, Depends(get_long_term_memory_manager)],
    search_documents: Annotated[SearchDocumentsUseCase, Depends(get_search_documents_use_case)],
    usage_repo: Annotated[PostgresUsageRepository, Depends(get_usage_repository)],
) -> SendMessageUseCase:
    return SendMessageUseCase(
        conversation_repo,
        message_repo,
        llm_provider,
        title_service,
        short_term_memory,
        long_term_memory,
        search_documents,
        usage_repo,
    )


# --- Multi-agent framework dependencies ---

from app.ai.agents.coordinator import CoordinatorAgent
from app.ai.agents.memory_agent import MemoryAgent
from app.ai.agents.planner import PlannerAgent
from app.ai.agents.research import ResearchAgent
from app.ai.agents.response_agent import ResponseAgent
from app.ai.agents.tool_agent import ToolAgent
from app.ai.tools.base import IToolExecutor
from app.ai.tools.stub_executor import StubToolExecutor
from app.application.use_cases.run_agent_pipeline import RunAgentPipelineUseCase
from app.infrastructure.database.repositories.postgres_agent_execution_repository import (
    PostgresAgentExecutionRepository,
)


from app.ai.tools.factory import get_tool_registry


def get_tool_executor() -> IToolExecutor:
    return get_tool_registry()


def get_coordinator_agent(
    llm_provider: Annotated[ILLMProvider, Depends(get_current_llm_provider)],
    long_term_memory: Annotated[LongTermMemoryManager, Depends(get_long_term_memory_manager)],
    tool_executor: Annotated[IToolExecutor, Depends(get_tool_executor)],
) -> CoordinatorAgent:
    return CoordinatorAgent(
        planner=PlannerAgent(llm_provider),
        memory_agent=MemoryAgent(long_term_memory),
        research_agent=ResearchAgent(tool_executor),
        tool_agent=ToolAgent(tool_executor),
        response_agent=ResponseAgent(llm_provider),
    )


def get_agent_execution_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PostgresAgentExecutionRepository:
    return PostgresAgentExecutionRepository(session)


def get_run_agent_pipeline_use_case(
    conversation_repo: Annotated[PostgresConversationRepository, Depends(get_conversation_repository)],
    message_repo: Annotated[PostgresMessageRepository, Depends(get_message_repository)],
    execution_repo: Annotated[PostgresAgentExecutionRepository, Depends(get_agent_execution_repository)],
    coordinator: Annotated[CoordinatorAgent, Depends(get_coordinator_agent)],
) -> RunAgentPipelineUseCase:
    return RunAgentPipelineUseCase(conversation_repo, message_repo, execution_repo, coordinator)
