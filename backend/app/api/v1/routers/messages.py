"""
api/v1/routers/messages.py

Why this file exists:
    HTTP boundary for message history and the streaming chat endpoint. The
    streaming endpoint is the most unusual handler in the codebase: instead
    of returning a Pydantic model, it returns a StreamingResponse that
    forwards Server-Sent Events as SendMessageUseCase yields them.
"""

import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import (
    get_current_user,
    get_message_repository,
    get_send_message_use_case,
)
from app.api.v1.schemas.chat_schemas import MessageResponse, SendMessageRequest
from app.application.use_cases.send_message import SendMessageUseCase
from app.domain.entities.user import User
from app.domain.exceptions.chat_exceptions import (
    ConversationAccessDeniedError,
    ConversationNotFoundError,
)
from app.infrastructure.database.repositories.postgres_chat_repository import PostgresMessageRepository

router = APIRouter(prefix="/conversations/{conversation_id}/messages", tags=["messages"])


@router.get("", response_model=list[MessageResponse])
async def list_messages(
    conversation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],  # noqa: ARG001 — enforces auth even though unused
    repo: Annotated[PostgresMessageRepository, Depends(get_message_repository)],
    limit: int = Query(default=50, le=200),
    before: UUID | None = None,
) -> list[MessageResponse]:
    messages = await repo.list_by_conversation(conversation_id, limit=limit, before=before)
    return [MessageResponse.model_validate(m) for m in messages]


async def _sse_event_stream(use_case: SendMessageUseCase, user_id: UUID, conversation_id: UUID, body: SendMessageRequest):
    """Formats each StreamedToken as an SSE `data: {...}` line. The
    frontend's fetch-based reader (Phase 10) parses these as JSON."""
    try:
        async for token in use_case.execute(
            user_id=user_id,
            conversation_id=conversation_id,
            content=body.content,
            model=body.model,
            document_ids=body.document_ids or None,
        ):
            payload = {"text": token.text, "done": token.done, "message_id": token.message_id}
            yield f"data: {json.dumps(payload)}\n\n"
    except (ConversationNotFoundError, ConversationAccessDeniedError) as exc:
        error_payload = {"error": str(exc)}
        yield f"data: {json.dumps(error_payload)}\n\n"


@router.post("", status_code=status.HTTP_200_OK)
async def send_message(
    conversation_id: UUID,
    body: SendMessageRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[SendMessageUseCase, Depends(get_send_message_use_case)],
) -> StreamingResponse:
    """Streams the assistant's reply as Server-Sent Events. Errors that
    occur before any token is emitted are also raised as normal
    HTTPExceptions where possible; errors during the stream are sent as an
    SSE error event since headers are already committed by then."""
    return StreamingResponse(
        _sse_event_stream(use_case, current_user.id, conversation_id, body),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
