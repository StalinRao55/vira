"""
domain/exceptions/auth_exceptions.py

Why this file exists:
    Use cases raise these instead of HTTPException — the domain/application
    layers must not know about HTTP status codes. The API layer catches
    these and translates them to the correct HTTP response.

How it communicates with other modules:
    - application/use_cases/* raise these
    - api/v1/routers/auth.py catches these and maps to HTTP status codes
"""


class AuthError(Exception):
    """Base class for all authentication-related domain errors."""


class EmailAlreadyRegisteredError(AuthError):
    def __init__(self, email: str):
        super().__init__(f"Email already registered: {email}")


class InvalidCredentialsError(AuthError):
    def __init__(self):
        super().__init__("Invalid email or password")


class InvalidTokenError(AuthError):
    def __init__(self, reason: str = "Invalid or expired token"):
        super().__init__(reason)


class UserNotFoundError(AuthError):
    def __init__(self):
        super().__init__("User not found")


class InvalidOAuthTokenError(AuthError):
    def __init__(self, reason: str = "Invalid or expired OAuth token"):
        super().__init__(reason)
