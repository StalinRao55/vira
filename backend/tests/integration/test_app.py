"""
tests/integration/test_app.py

Why this file exists:
    Unit tests (tests/unit/) exercise use cases in isolation with in-memory
    fakes — fast, but they never prove the routers/middleware/DI wiring in
    main.py actually works together. This uses FastAPI's TestClient against
    the REAL app instance, proving: middleware runs (X-Request-ID header
    appears), routing resolves, and auth correctly rejects unauthenticated
    requests before reaching any use case.

    NOTE: full request/response tests that touch the database require a
    live Postgres instance (the ORM models use Postgres-specific types —
    UUID, JSONB — so SQLite can't substitute). Those are exactly the tests
    Phase 13's CI pipeline runs against a real Postgres service container;
    here we cover what's meaningfully testable without one.
"""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/x")
os.environ.setdefault("JWT_SECRET_KEY", "test_secret_key_for_integration_tests")
os.environ.setdefault("ENVIRONMENT", "test")

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_metrics_endpoint_is_reachable():
    response = client.get("/metrics")
    assert response.status_code == 200


def test_request_tracing_middleware_adds_request_id_header():
    response = client.get("/health")
    assert "X-Request-ID" in response.headers


def test_openapi_schema_lists_all_routers():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/conversations" in paths
    assert "/api/v1/memories" in paths
    assert "/api/v1/documents" in paths
    assert "/api/v1/tools" in paths
    assert "/api/v1/analytics/usage" in paths


def test_protected_route_rejects_missing_auth():
    response = client.get("/api/v1/conversations")
    assert response.status_code in (401, 403)


def test_protected_route_rejects_invalid_token():
    response = client.get("/api/v1/conversations", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_register_validates_email_format():
    response = client.post("/api/v1/auth/register", json={"email": "not-an-email", "password": "somepassword123"})
    assert response.status_code == 422


def test_register_validates_password_length():
    response = client.post("/api/v1/auth/register", json={"email": "valid@example.com", "password": "short"})
    assert response.status_code == 422
