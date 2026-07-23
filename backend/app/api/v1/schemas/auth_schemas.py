"""
api/v1/schemas/auth_schemas.py

Why this file exists:
    Defines exactly what the API accepts and returns over HTTP. Kept
    separate from domain.entities.User so that, e.g., we can add a
    "display_name" to the API response without touching the domain model,
    or hide internal fields (hashed_password!) that must never be
    serialized to a client.

How it communicates with other modules:
    - api/v1/routers/auth.py uses these for request validation and
      response_model
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: UUID
    email: str
    role: str
    is_email_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class OAuthCallbackRequest(BaseModel):
    code: str
    state: str | None = None


class OAuthUrlRequest(BaseModel):
    """Request for getting Google OAuth authorization URL."""

    redirect_uri: str = Field(default_factory=lambda: None)  # Optional override


class RequestPasswordResetRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)
