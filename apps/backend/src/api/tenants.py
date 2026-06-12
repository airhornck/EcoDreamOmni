"""Tenant Management API — W23.

Routes:
  POST /tenants              — Create tenant
  GET  /tenants              — List tenants
  GET  /tenants/{tenant_id}  — Get tenant detail
  PATCH /tenants/{tenant_id} — Update tenant
  DELETE /tenants/{tenant_id} — Delete tenant
  GET  /tenants/{tenant_id}/config — Get config
  PATCH /tenants/{tenant_id}/config — Update config
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from src.core.tenant_middleware import get_current_tenant_id, require_tenant
from src.services import tenant_service

router = APIRouter(prefix="/tenants", tags=["tenants"])


# ─── Schemas ───

class CreateTenantRequest(BaseModel):
    name: str
    slug: str
    config: Dict[str, Any] = {}
    allowed_platforms: List[str] = ["xhs"]
    max_accounts: int = 50


class UpdateTenantRequest(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    max_accounts: Optional[int] = None
    allowed_platforms: Optional[List[str]] = None


class ConfigUpdateRequest(BaseModel):
    key: str
    value: Any


class TenantResponse(BaseModel):
    tenant_id: str
    name: str
    slug: str
    status: str
    allowed_platforms: List[str]
    max_accounts: int
    created_at: str
    updated_at: str


# ─── Routes ───

@router.post("", status_code=201, response_model=TenantResponse)
def create_tenant(req: CreateTenantRequest):
    try:
        tenant = tenant_service.create_tenant(
            name=req.name,
            slug=req.slug,
            config=req.config,
            allowed_platforms=req.allowed_platforms,
            max_accounts=req.max_accounts,
        )
        return _to_response(tenant)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("", response_model=List[TenantResponse])
def list_tenants(status: Optional[str] = None):
    return [_to_response(t) for t in tenant_service.list_tenants(status)]


@router.get("/{tenant_id}", response_model=TenantResponse)
def get_tenant(tenant_id: str):
    tenant = tenant_service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return _to_response(tenant)


@router.patch("/{tenant_id}", response_model=TenantResponse)
def update_tenant(tenant_id: str, req: UpdateTenantRequest):
    tenant = tenant_service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    update_data = req.model_dump(exclude_unset=True)
    updated = tenant_service.update_tenant(tenant_id, **update_data)
    return _to_response(updated)


@router.delete("/{tenant_id}", status_code=204)
def delete_tenant(tenant_id: str):
    ok = tenant_service.delete_tenant(tenant_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return None


# ─── Config ───

@router.get("/{tenant_id}/config")
def get_tenant_config(tenant_id: str, key: Optional[str] = None):
    tenant = tenant_service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    if key:
        return {"key": key, "value": tenant.config.get(key)}
    return {"config": tenant.config}


@router.patch("/{tenant_id}/config")
def update_tenant_config(tenant_id: str, req: ConfigUpdateRequest):
    ok = tenant_service.set_tenant_config(tenant_id, req.key, req.value)
    if not ok:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"key": req.key, "value": req.value}


# ─── Current tenant context (for any authenticated route) ───

@router.get("/context/whoami")
def whoami(request: Request):
    """Return current tenant context from request."""
    tenant_id = get_current_tenant_id(request)
    if not tenant_id:
        return {"tenant_id": None, "authenticated": False}
    tenant = tenant_service.get_tenant(tenant_id)
    if not tenant:
        return {"tenant_id": tenant_id, "authenticated": True, "tenant_found": False}
    return {
        "tenant_id": tenant_id,
        "tenant_name": tenant.name,
        "tenant_slug": tenant.slug,
        "authenticated": True,
    }


def _to_response(tenant: tenant_service.Tenant) -> TenantResponse:
    return TenantResponse(
        tenant_id=tenant.tenant_id,
        name=tenant.name,
        slug=tenant.slug,
        status=tenant.status,
        allowed_platforms=tenant.allowed_platforms,
        max_accounts=tenant.max_accounts,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
    )
