"""
api/v1/routers/tools.py

Why this file exists:
    Exposes the tool registry over HTTP: list what's available (for a
    "tool selector" UI element per the spec) and directly invoke one
    (useful for testing a tool or building a non-chat tool-use UI).
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.ai.tools.base import IToolExecutor
from app.ai.tools.factory import get_tool_registry
from app.api.v1.dependencies import get_current_user, get_tool_executor
from app.domain.entities.user import User

router = APIRouter(prefix="/tools", tags=["tools"])


class ToolInvokeRequest(BaseModel):
    arguments: dict = {}


class ToolInvokeResponse(BaseModel):
    output: str
    success: bool
    error: str | None = None


@router.get("")
async def list_tools(current_user: Annotated[User, Depends(get_current_user)]) -> dict[str, str]:
    return get_tool_registry().descriptions()


@router.post("/{tool_name}/invoke", response_model=ToolInvokeResponse)
async def invoke_tool(
    tool_name: str,
    body: ToolInvokeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    tool_executor: Annotated[IToolExecutor, Depends(get_tool_executor)],
) -> ToolInvokeResponse:
    result = await tool_executor.execute(tool_name, body.arguments)
    return ToolInvokeResponse(output=result.output, success=result.success, error=result.error)
