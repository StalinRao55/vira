"""
main.py

Why this file exists:
    The application entry point / composition root. Creates the FastAPI
    app, configures CORS for the Next.js frontend, and mounts routers. Kept
    intentionally thin — no business logic, just wiring.

How it communicates with other modules:
    - Mounts api/v1/routers/auth (and, in later phases, conversations,
      messages, memory, agents, tools, admin)
    - Reads app/core/config.settings for CORS origin and environment
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routers import agents, analytics, auth, conversations, documents, memory, messages, tools
from app.api.middleware.request_tracing import RequestTracingMiddleware
from app.core.logging_config import configure_logging
from app.core.config import settings

configure_logging(settings.environment)

app = FastAPI(title="VIRA API", version="0.1.0")

app.add_middleware(RequestTracingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(conversations.router, prefix="/api/v1")
app.include_router(messages.router, prefix="/api/v1")
app.include_router(memory.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(tools.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Liveness/readiness probe for orchestrators (Docker/Kubernetes)."""
    return {"status": "ok"}


@app.get("/metrics")
async def metrics() -> dict[str, str]:
    """Placeholder metrics endpoint. In production, replace with a real
    Prometheus exporter (prometheus-fastapi-instrumentator) that tracks
    request counts/latencies/error rates automatically — noted as a
    Phase 13 deployment addition rather than hand-rolled here."""
    return {"status": "metrics endpoint - wire prometheus-fastapi-instrumentator in production"}
