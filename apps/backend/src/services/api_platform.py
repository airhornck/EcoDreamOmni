"""API Platform — W25: API Keys, Webhooks, Rate Limiting.

Features:
  - API Key generation and revocation
  - Webhook endpoint registration
  - Simple token-bucket rate limiting (in-memory)
"""

import secrets
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class APIKey:
    key_id: str
    tenant_id: str
    key_hash: str
    name: str
    permissions: List[str]
    created_at: str
    expires_at: Optional[str]
    revoked: bool = False


@dataclass
class Webhook:
    webhook_id: str
    tenant_id: str
    url: str
    events: List[str]
    secret: str
    active: bool = True


_api_keys: Dict[str, APIKey] = {}       # key_id → APIKey
_key_hash_index: Dict[str, str] = {}    # key_hash → key_id
_webhooks: Dict[str, Webhook] = {}      # webhook_id → Webhook

# Rate limiting: tenant_id → {endpoint → [timestamps]}
_rate_limit_buckets: Dict[str, Dict[str, List[float]]] = {}


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def create_api_key(
    tenant_id: str,
    name: str,
    permissions: List[str] = None,
    expires_days: Optional[int] = None,
) -> Dict[str, str]:
    """Generate a new API key. Returns the raw key (shown once)."""
    raw_key = f"edo_{secrets.token_urlsafe(32)}"
    key_hash = secrets.token_urlsafe(16)
    key_id = f"key_{secrets.token_urlsafe(8)}"

    from datetime import datetime, timezone, timedelta
    expires = None
    if expires_days:
        expires = (datetime.now(timezone.utc) + timedelta(days=expires_days)).isoformat()

    api_key = APIKey(
        key_id=key_id,
        tenant_id=tenant_id,
        key_hash=key_hash,
        name=name,
        permissions=permissions or ["read"],
        created_at=_now(),
        expires_at=expires,
    )
    _api_keys[key_id] = api_key
    _key_hash_index[key_hash] = key_id

    return {"key_id": key_id, "api_key": raw_key, "name": name}


def validate_api_key(key_hash: str) -> Optional[APIKey]:
    key_id = _key_hash_index.get(key_hash)
    if not key_id:
        return None
    key = _api_keys.get(key_id)
    if not key or key.revoked:
        return None
    if key.expires_at:
        from datetime import datetime, timezone
        if datetime.now(timezone.utc).isoformat() > key.expires_at:
            return None
    return key


def revoke_api_key(key_id: str) -> bool:
    key = _api_keys.get(key_id)
    if key:
        key.revoked = True
        return True
    return False


def list_api_keys(tenant_id: str) -> List[APIKey]:
    return [k for k in _api_keys.values() if k.tenant_id == tenant_id]


# ─── Webhooks ───

def register_webhook(
    tenant_id: str,
    url: str,
    events: List[str],
) -> Webhook:
    webhook_id = f"wh_{secrets.token_urlsafe(8)}"
    webhook = Webhook(
        webhook_id=webhook_id,
        tenant_id=tenant_id,
        url=url,
        events=events,
        secret=secrets.token_urlsafe(16),
    )
    _webhooks[webhook_id] = webhook
    return webhook


def list_webhooks(tenant_id: str) -> List[Webhook]:
    return [w for w in _webhooks.values() if w.tenant_id == tenant_id]


def delete_webhook(webhook_id: str) -> bool:
    return _webhooks.pop(webhook_id, None) is not None


# ─── Rate Limiting ───

def check_rate_limit(
    tenant_id: str,
    endpoint: str,
    max_requests: int = 100,
    window_seconds: int = 60,
) -> Dict[str, Any]:
    """Token-bucket style rate limit check."""
    now = time.time()
    bucket = _rate_limit_buckets.setdefault(tenant_id, {}).setdefault(endpoint, [])

    # Remove old timestamps outside window
    bucket[:] = [t for t in bucket if now - t < window_seconds]

    if len(bucket) >= max_requests:
        return {
            "allowed": False,
            "limit": max_requests,
            "remaining": 0,
            "reset_in": round(window_seconds - (now - bucket[0]), 1),
        }

    bucket.append(now)
    return {
        "allowed": True,
        "limit": max_requests,
        "remaining": max_requests - len(bucket),
    }
