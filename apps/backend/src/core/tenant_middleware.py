"""Tenant Middleware — W23: inject tenant context into every request.

Extraction priority:
  1. X-Tenant-ID header (for service-to-service)
  2. JWT payload 'tenant_id' claim (for user requests)
  3. X-Tenant-Slug header (fallback)

Injected into:
  - request.state.tenant_id
  - response headers X-Tenant-ID (for debugging)
"""

from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.security import decode_token
from src.services import tenant_service


class TenantContextMiddleware(BaseHTTPMiddleware):
    """Extract tenant_id from request and attach to state."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        tenant_id = self._extract_tenant_id(request)
        request.state.tenant_id = tenant_id

        response = await call_next(request)

        if tenant_id:
            response.headers["X-Tenant-ID"] = tenant_id
        return response

    def _extract_tenant_id(self, request: Request) -> Optional[str]:
        # Priority 1: Header
        header_tid = request.headers.get("X-Tenant-ID")
        if header_tid:
            return header_tid

        # Priority 2: JWT Bearer token
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            payload = decode_token(token)
            if payload:
                jwt_tid = payload.get("tenant_id")
                if jwt_tid:
                    return jwt_tid

        # Priority 3: Slug header → lookup
        slug = request.headers.get("X-Tenant-Slug")
        if slug:
            tenant = tenant_service.get_tenant_by_slug(slug)
            if tenant:
                return tenant.tenant_id

        return None


def get_current_tenant_id(request: Request) -> Optional[str]:
    """Dependency to get tenant_id from request state."""
    return getattr(request.state, "tenant_id", None)


def require_tenant(request: Request) -> str:
    """Dependency that raises 401 if no tenant_id in context."""
    tenant_id = get_current_tenant_id(request)
    if not tenant_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Tenant context required")
    # Validate tenant exists and is active
    tenant = tenant_service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=401, detail="Tenant not found")
    if tenant.status != "active":
        raise HTTPException(status_code=403, detail=f"Tenant status: {tenant.status}")
    return tenant_id
