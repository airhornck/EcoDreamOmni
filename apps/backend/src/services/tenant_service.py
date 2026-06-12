"""Tenant Service — W23: multi-tenancy isolation layer.

Features:
  - Tenant CRUD (brand-level isolation)
  - Tenant-scoped configuration overrides
  - Platform rule per-tenant versioning
  - Data isolation: all in-memory stores filter by tenant_id

Constraints:
  - Phase 3 MVP: in-memory tenant gating on service layer
  - PostgreSQL row-level security deferred to production migration
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import secrets


@dataclass
class Tenant:
    tenant_id: str
    name: str
    slug: str  # URL-safe identifier
    status: str = "active"  # active | suspended | trial_expired
    config: Dict[str, Any] = field(default_factory=dict)
    allowed_platforms: List[str] = field(default_factory=lambda: ["xhs"])
    max_accounts: int = 50
    created_at: str = ""
    updated_at: str = ""


# In-memory tenant store
tenant_db: Dict[str, Tenant] = {}  # tenant_id → Tenant
tenant_slug_index: Dict[str, str] = {}  # slug → tenant_id


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_tenant(
    name: str,
    slug: str,
    config: Optional[Dict[str, Any]] = None,
    allowed_platforms: Optional[List[str]] = None,
    max_accounts: int = 50,
) -> Tenant:
    if slug in tenant_slug_index:
        raise ValueError(f"Tenant slug '{slug}' already exists")

    tenant_id = f"tnt_{secrets.token_urlsafe(8)}"
    now = _now()
    tenant = Tenant(
        tenant_id=tenant_id,
        name=name,
        slug=slug,
        status="active",
        config=config or {},
        allowed_platforms=allowed_platforms or ["xhs"],
        max_accounts=max_accounts,
        created_at=now,
        updated_at=now,
    )
    tenant_db[tenant_id] = tenant
    tenant_slug_index[slug] = tenant_id
    return tenant


def get_tenant(tenant_id: str) -> Optional[Tenant]:
    return tenant_db.get(tenant_id)


def get_tenant_by_slug(slug: str) -> Optional[Tenant]:
    tid = tenant_slug_index.get(slug)
    return tenant_db.get(tid) if tid else None


def list_tenants(status: Optional[str] = None) -> List[Tenant]:
    tenants = list(tenant_db.values())
    if status:
        tenants = [t for t in tenants if t.status == status]
    return tenants


def update_tenant(tenant_id: str, **kwargs) -> Optional[Tenant]:
    tenant = tenant_db.get(tenant_id)
    if not tenant:
        return None
    for key, value in kwargs.items():
        if hasattr(tenant, key):
            setattr(tenant, key, value)
    tenant.updated_at = _now()
    return tenant


def delete_tenant(tenant_id: str) -> bool:
    tenant = tenant_db.pop(tenant_id, None)
    if tenant:
        tenant_slug_index.pop(tenant.slug, None)
        return True
    return False


def is_platform_allowed(tenant_id: str, platform: str) -> bool:
    tenant = tenant_db.get(tenant_id)
    if not tenant:
        return False
    return platform.lower() in [p.lower() for p in tenant.allowed_platforms]


def can_add_account(tenant_id: str, current_account_count: int) -> bool:
    tenant = tenant_db.get(tenant_id)
    if not tenant:
        return False
    return current_account_count < tenant.max_accounts


# ─── Tenant-scoped configuration overrides ───

def get_tenant_config(tenant_id: str, key: str, default: Any = None) -> Any:
    tenant = tenant_db.get(tenant_id)
    if not tenant:
        return default
    return tenant.config.get(key, default)


def set_tenant_config(tenant_id: str, key: str, value: Any) -> bool:
    tenant = tenant_db.get(tenant_id)
    if not tenant:
        return False
    tenant.config[key] = value
    tenant.updated_at = _now()
    return True
