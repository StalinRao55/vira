"""
core/security.py

Why this file exists:
    Centralizes every cryptographic operation (password hashing, JWT
    signing/verification) in one place. Nothing else in the app should
    import `jwt` or `passlib` directly — this keeps a security review to a
    single file, and lets us swap the hashing algorithm or token library
    later without touching business logic.

How it communicates with other modules:
    - application/use_cases/login_user.py and register_user.py call
      hash_password / verify_password
    - application/use_cases/login_user.py and refresh_token.py call
      create_access_token / create_refresh_token
    - api/v1/dependencies.py calls decode_token to authenticate requests
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password with bcrypt before storing it. Never store
    plaintext passwords, ever."""
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compare a plaintext password against a stored bcrypt hash."""
    return _pwd_context.verify(plain_password, hashed_password)


def _create_token(subject: str, token_type: TokenType, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type.value,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: str) -> str:
    """Short-lived token sent on every authenticated request."""
    return _create_token(
        subject=user_id,
        token_type=TokenType.ACCESS,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(user_id: str) -> str:
    """Long-lived token used only to mint new access tokens, never sent to
    business endpoints directly."""
    return _create_token(
        subject=user_id,
        token_type=TokenType.REFRESH,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str, expected_type: TokenType) -> str:
    """Decode and validate a JWT, returning the user_id (subject).

    Raises jwt.PyJWTError (or subclasses) on any invalid/expired/wrong-type
    token — callers are expected to translate that into an HTTP 401.
    """
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    if payload.get("type") != expected_type.value:
        raise jwt.InvalidTokenError(f"Expected token type '{expected_type.value}'")
    return payload["sub"]
