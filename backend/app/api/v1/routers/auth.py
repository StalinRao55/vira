"""
api/v1/routers/auth.py

Why this file exists:
    The HTTP boundary for registration, login, token refresh, and "who am
    I". Every handler follows the same shape: validate (Pydantic already
    did this), call a use case, catch domain exceptions, return a schema.
    No business logic lives here.

How it communicates with other modules:
    - Depends on api/v1/dependencies for use case + current-user injection
    - Depends on api/v1/schemas/auth_schemas for request/response shapes
    - Catches app/domain/exceptions/auth_exceptions
"""

import logging
from typing import Annotated
import urllib.parse

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.dependencies import (
    get_current_user,
    get_login_use_case,
    get_oauth_use_case,
    get_refresh_use_case,
    get_register_use_case,
    get_request_password_reset_use_case,
    get_reset_password_use_case,
)
from app.api.v1.schemas.auth_schemas import (
    LoginRequest,
    OAuthCallbackRequest,
    OAuthUrlRequest,
    RefreshRequest,
    RegisterRequest,
    RequestPasswordResetRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)
from app.application.use_cases.login_user import LoginUserUseCase
from app.application.use_cases.oauth_user import OAuthUserUseCase
from app.application.use_cases.refresh_token import RefreshTokenUseCase
from app.application.use_cases.register_user import RegisterUserUseCase
from app.application.use_cases.request_password_reset import RequestPasswordResetUseCase
from app.application.use_cases.reset_password import ResetPasswordUseCase
from app.core.config import settings
from app.domain.entities.user import User
from app.domain.exceptions.auth_exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidOAuthTokenError,
    InvalidTokenError,
    UserNotFoundError,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    use_case: Annotated[RegisterUserUseCase, Depends(get_register_use_case)],
) -> UserResponse:
    try:
        user = await use_case.execute(email=body.email, password=body.password)
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    use_case: Annotated[LoginUserUseCase, Depends(get_login_use_case)],
) -> TokenResponse:
    try:
        tokens = await use_case.execute(email=body.email, password=body.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return TokenResponse(access_token=tokens.access_token, refresh_token=tokens.refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    use_case: Annotated[RefreshTokenUseCase, Depends(get_refresh_use_case)],
) -> TokenResponse:
    try:
        tokens = await use_case.execute(refresh_token=body.refresh_token)
    except (InvalidTokenError, UserNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return TokenResponse(access_token=tokens.access_token, refresh_token=tokens.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(current_user: Annotated[User, Depends(get_current_user)]) -> None:
    # Stateless JWT logout: the client discards its tokens. If you need
    # server-side revocation (e.g. "log out of all devices"), Phase 13's
    # Redis instance is the natural place for a token blocklist keyed by
    # jti with TTL = token expiry.
    logger.info("User logged out: %s", current_user.id)


@router.get("/oauth/google/url")
async def get_google_oauth_url(request: OAuthUrlRequest) -> dict[str, str]:
    """Get the Google OAuth authorization URL to redirect the user to."""
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Google OAuth is not configured")

    redirect_uri = request.redirect_uri or settings.google_redirect_uri
    if not redirect_uri:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No redirect_uri configured")

    # Build the Google OAuth authorization URL
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
    }
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return {"url": auth_url}


@router.post("/oauth/google/callback", response_model=TokenResponse)
async def google_oauth_callback(
    body: OAuthCallbackRequest,
    use_case: Annotated[OAuthUserUseCase, Depends(get_oauth_use_case)],
) -> TokenResponse:
    """Handle Google OAuth callback: exchange code for ID token and return JWT."""
    try:
        tokens = await use_case.execute(authorization_code=body.code)
    except InvalidOAuthTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return TokenResponse(access_token=tokens.access_token, refresh_token=tokens.refresh_token)


@router.post("/password/request-reset", status_code=status.HTTP_200_OK)
async def request_password_reset(
    body: RequestPasswordResetRequest,
    use_case: Annotated[RequestPasswordResetUseCase, Depends(get_request_password_reset_use_case)],
) -> dict[str, str]:
    """Request a password reset. In production, sends email with reset link."""
    token = await use_case.execute(email=body.email)
    # In production, the token would be sent via email and not returned here
    if token:
        return {"message": "If the email exists, a password reset link will be sent."}
    return {"message": "If the email exists, a password reset link will be sent."}


@router.post("/password/reset", status_code=status.HTTP_200_OK)
async def reset_password(
    body: ResetPasswordRequest,
    use_case: Annotated[ResetPasswordUseCase, Depends(get_reset_password_use_case)],
) -> dict[str, str]:
    """Reset password using a reset token."""
    try:
        await use_case.execute(token=body.token, new_password=body.new_password)
        return {"message": "Password reset successful"}
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
