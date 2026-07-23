"""
application/use_cases/oauth_user.py

Why this file exists:
    Encapsulates the "authenticate via Google OAuth" workflow. Exchanges
    an OAuth authorization code for an ID token, validates it, and either
    creates a new user or logs in an existing one.

How it communicates with other modules:
    - Depends on IUserRepository (interface, injected)
    - Depends on core/security (create_access_token, create_refresh_token)
    - Depends on core/config (Google OAuth settings)
    - Raises InvalidOAuthTokenError or GoogleOAuthError (domain/exceptions)
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
from google.auth.transport.requests import Request
from google.oauth2.id_token import verify_oauth2_token

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.domain.entities.user import User
from app.domain.exceptions.auth_exceptions import InvalidOAuthTokenError
from app.domain.repositories.user_repository import IUserRepository

logger = logging.getLogger(__name__)


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str


class OAuthUserUseCase:
    """Handle Google OAuth flow: exchange code for ID token, verify it,
    and create/login the user."""

    def __init__(self, user_repository: IUserRepository):
        self._user_repository = user_repository

    async def execute(self, authorization_code: str) -> TokenPair:
        """Exchange Google authorization code for ID token and mint JWT tokens."""
        if not settings.google_client_id or not settings.google_client_secret:
            logger.error("Google OAuth not configured")
            raise InvalidOAuthTokenError("Google OAuth is not configured")

        # Exchange authorization code for ID token
        id_token = await self._exchange_code_for_id_token(authorization_code)

        # Verify the ID token and extract user info
        user_info = self._verify_id_token(id_token)

        # Find or create user
        user = await self._get_or_create_user(user_info)

        logger.info("User authenticated via Google OAuth: %s", user.id)
        return TokenPair(
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(str(user.id)),
        )

    async def _exchange_code_for_id_token(self, authorization_code: str) -> str:
        """Exchange authorization code with Google for ID token."""
        token_endpoint = "https://oauth2.googleapis.com/token"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_endpoint,
                data={
                    "code": authorization_code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": settings.google_redirect_uri,
                    "grant_type": "authorization_code",
                },
            )

        if response.status_code != 200:
            logger.error("Failed to exchange authorization code: %s", response.text)
            raise InvalidOAuthTokenError("Failed to exchange authorization code with Google")

        data = response.json()
        id_token = data.get("id_token")
        if not id_token:
            logger.error("No ID token in Google response")
            raise InvalidOAuthTokenError("No ID token in Google response")

        return id_token

    def _verify_id_token(self, id_token: str) -> dict:
        """Verify Google ID token and extract claims."""
        try:
            # Verify the ID token signature and get claims
            claims = verify_oauth2_token(id_token, Request(), settings.google_client_id)

            # Verify the token hasn't expired
            if claims.get("exp", 0) < datetime.now(timezone.utc).timestamp():
                raise InvalidOAuthTokenError("ID token has expired")

            return claims
        except Exception as exc:
            logger.exception("Failed to verify ID token: %s", str(exc))
            raise InvalidOAuthTokenError("Invalid ID token") from exc

    async def _get_or_create_user(self, user_info: dict) -> User:
        """Find existing user by oauth_id, or create a new one."""
        oauth_id = user_info.get("sub")
        email = user_info.get("email")

        if not oauth_id:
            raise InvalidOAuthTokenError("No subject claim in ID token")

        # Try to find by OAuth ID first
        user = await self._user_repository.get_by_oauth_id("google", oauth_id)
        if user:
            return user

        # Try to find by email (user may have registered with email/password first)
        if email:
            user = await self._user_repository.get_by_email(email)
            if user:
                # Link OAuth account to existing user
                user.oauth_provider = "google"
                user.oauth_id = oauth_id
                await self._user_repository.update(user)
                logger.info("Linked Google OAuth to existing user: %s", user.id)
                return user

        # Create new user
        user = User(
            email=email or f"user_{oauth_id}@oauth.google",
            oauth_provider="google",
            oauth_id=oauth_id,
            hashed_password=None,  # OAuth users have no password
        )
        created_user = await self._user_repository.create(user)
        logger.info("Created new user from Google OAuth: %s", created_user.id)
        return created_user
