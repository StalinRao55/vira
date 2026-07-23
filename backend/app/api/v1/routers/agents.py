"""
api/v1/routers/agents.py

Why this file exists:
    Exposes agent-mode chat as its own endpoint (rather than a flag on the
    regular send endpoint) since its SSE event shape differs — it emits
    intermediate "agent_step" events (planner ran, memory ran, ...) before
    the response tokens, which the frontend can render as a visible
    "thinking" trace.
"""

import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user, get_run_agent_pipeline_use_case
from app.api.v1.schemas.chat_schemas import SendMessageRequest
from app.application.use_cases.run_agent_pipeline import RunAgentPipelineUseCase
from app.domain.entities.user import User
from app.domain.exceptions.chat_exceptions import ConversationAccessDeniedError, ConversationNotFoundError

router = APIRouter(prefix="/conversations/{conversation_id}/agent-messages", tags=["agents"])


async def _sse_stream(use_case: RunAgentPipelineUseCase, user_id: UUID, conversation_id: UUID, body: SendMessageRequest):
    try:
        async for event in use_case.execute(
            user_id=user_id, conversation_id=conversation_id, content=body.content, model=body.model
        ):
            payload = {
                "text": event.text,
                "done": event.done,
                "message_id": event.message_id,
                "agent_step": event.agent_step,
            }
            yield f"data: {json.dumps(payload)}\n\n"
    except (ConversationNotFoundError, ConversationAccessDeniedError) as exc:
        yield f"data: {json.dumps({'error': str(exc)})}\n\n"


@router.post("", status_code=status.HTTP_200_OK)
async def send_agent_message(
    conversation_id: UUID,
    body: SendMessageRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[RunAgentPipelineUseCase, Depends(get_run_agent_pipeline_use_case)],
) -> StreamingResponse:
    return StreamingResponse(
        _sse_stream(use_case, current_user.id, conversation_id, body),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
