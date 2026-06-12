"""API Platform API — W25.

Routes:
  POST /api-platform/keys           — Create API key
  GET  /api-platform/keys           — List API keys
  DELETE /api-platform/keys/{kid}   — Revoke API key
  POST /api-platform/webhooks       — Register webhook
  GET  /api-platform/webhooks       — List webhooks
  DELETE /api-platform/webhooks/{wid} — Delete webhook
  GET  /api-platform/rate-limit     — Check rate limit status
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from src.services import api_platform as ap
from src.core.tenant_middleware import require_tenant

router = APIRouter(prefix="/api-platform", tags=["api-platform"])


class CreateKeyRequest(BaseModel):
    name: str
    permissions: List[str] = ["read"]
    expires_days: Optional[int] = None


class RegisterWebhookRequest(BaseModel):
    url: str
    events: List[str]


@router.post("/keys")
def create_key(req: CreateKeyRequest, tenant_id: str = require_tenant):
    result = ap.create_api_key(
        tenant_id=tenant_id,
        name=req.name,
        permissions=req.permissions,
        expires_days=req.expires_days,
    )
    return result


@router.get("/keys")
def list_keys(tenant_id: str = require_tenant):
    keys = ap.list_api_keys(tenant_id)
    return [
        {
            "key_id": k.key_id,
            "name": k.name,
            "permissions": k.permissions,
            "created_at": k.created_at,
            "expires_at": k.expires_at,
            "revoked": k.revoked,
        }
        for k in keys
    ]


@router.delete("/keys/{key_id}")
def revoke_key(key_id: str):
    ok = ap.revoke_api_key(key_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"revoked": True}


@router.post("/webhooks")
def register_webhook(req: RegisterWebhookRequest, tenant_id: str = require_tenant):
    wh = ap.register_webhook(tenant_id, req.url, req.events)
    return {
        "webhook_id": wh.webhook_id,
        "url": wh.url,
        "events": wh.events,
        "secret": wh.secret,
    }


@router.get("/webhooks")
def list_webhooks(tenant_id: str = require_tenant):
    webhooks = ap.list_webhooks(tenant_id)
    return [
        {
            "webhook_id": w.webhook_id,
            "url": w.url,
            "events": w.events,
            "active": w.active,
        }
        for w in webhooks
    ]


@router.delete("/webhooks/{webhook_id}")
def delete_webhook(webhook_id: str):
    ok = ap.delete_webhook(webhook_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"deleted": True}


@router.get("/rate-limit")
def rate_limit_status(endpoint: str = "default", tenant_id: str = require_tenant):
    return ap.check_rate_limit(tenant_id, endpoint)
