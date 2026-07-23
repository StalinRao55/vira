"""
core/config.py

Why this file exists:
    Every module that needs an environment-driven value (DB URL, JWT secret,
    API keys) should import `settings` from here instead of calling
    `os.getenv` directly. This gives us one validated, typed source of truth
    and makes misconfiguration fail fast at startup instead of silently at
    runtime.

How it communicates with other modules:
    - infrastructure/database/base.py reads settings.database_url
    - core/security.py reads the JWT settings
    - ai/providers/* read the provider API keys
    - main.py reads settings.environment / settings.frontend_url for CORS
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application configuration, populated from environment
    variables / .env file. Pydantic validates types at startup."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = ""

    # AI providers
    gemini_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # App
    environment: str = "development"
    frontend_url: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    """Cached so we parse the environment once per process, not on every
    request. FastAPI dependencies should call this rather than instantiating
    Settings() directly."""
    return Settings()


settings = get_settings()
