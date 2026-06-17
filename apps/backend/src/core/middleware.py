"""FastAPI middleware aligned with detailed design §3.2 and §3.3.

- Request-ID generation and propagation
- Structured logging with content_id / account_id / request_id
- Error code injection
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Generate X-Request-ID for every request; propagate if client provided one."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        start = time.perf_counter()

        response = await call_next(request)

        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = str(latency_ms)
        return response


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Attach structured context to request state for downstream use.

    MVP: stores request_id on state; services can read request.state.request_id.
    Phase 2+: integrate with real structured logger (structlog / loguru).
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Ensure request_id exists (should be set by RequestIDMiddleware first)
        if not hasattr(request.state, "request_id"):
            request.state.request_id = str(uuid.uuid4())
        return await call_next(request)
