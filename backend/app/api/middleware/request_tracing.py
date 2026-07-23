"""
api/middleware/request_tracing.py

Why this file exists:
    Assigns a unique request ID to every incoming request (returned in the
    X-Request-ID response header, so a user-reported issue can be traced
    to exact log lines) and logs method/path/status/latency for every
    call — the request tracing / baseline observability requirement.
"""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("vira.requests")


class RequestTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start = time.monotonic()

        response = await call_next(request)

        latency_ms = int((time.monotonic() - start) * 1000)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "%s %s -> %d (%dms) [%s]",
            request.method,
            request.url.path,
            response.status_code,
            latency_ms,
            request_id,
        )
        return response
