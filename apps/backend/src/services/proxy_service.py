"""Proxy service: CRUD, health checks, and requests-compatible proxy dict builder.

V2.7.1+ — Added database persistence layer. Memory cache is primary,
DB is the durable source of truth loaded at startup.
"""

import logging
from typing import Dict, List, Optional

from src.models.proxy_config import (
    ProxyConfigEntry,
    create_proxy_entry,
    delete_proxy_entry,
    get_proxy_entry,
    list_proxy_entries,
    update_proxy_entry,
)

logger = logging.getLogger(__name__)

# ─── Sync CRUD (memory-first, callers see immediate results) ───


def create_proxy(
    name: str,
    provider: str,
    protocol: str,
    host: str,
    port: int,
    username: str = "",
    password: str = "",
    region: str = "",
    rotation_type: str = "static",
) -> ProxyConfigEntry:
    """Create a new proxy configuration entry (memory only)."""
    return create_proxy_entry(
        name=name,
        provider=provider,
        protocol=protocol,
        host=host,
        port=port,
        username=username,
        password=password,
        region=region,
        rotation_type=rotation_type,
    )


def list_proxies(active_only: bool = False) -> List[ProxyConfigEntry]:
    return list_proxy_entries(active_only=active_only)


def get_proxy(entry_id: str) -> Optional[ProxyConfigEntry]:
    return get_proxy_entry(entry_id)


def update_proxy(entry_id: str, **kwargs) -> Optional[ProxyConfigEntry]:
    return update_proxy_entry(entry_id, **kwargs)


def remove_proxy(entry_id: str) -> bool:
    return delete_proxy_entry(entry_id)


# ─── Persistence layer (async DB operations) ───


async def persist_proxy_to_db(db, entry: ProxyConfigEntry) -> None:
    """Save or update a proxy entry in the database."""
    from sqlalchemy import select
    from src.models.proxy_config_orm import ProxyConfigORM
    from datetime import datetime, timezone

    result = await db.execute(select(ProxyConfigORM).where(ProxyConfigORM.id == entry.id))
    orm = result.scalar_one_or_none()

    def _parse_dt(value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            # Handle ISO format with or without Z suffix
            v = value.replace("Z", "+00:00")
            try:
                return datetime.fromisoformat(v)
            except ValueError:
                return None
        return None

    now = datetime.now(timezone.utc)
    if orm is None:
        orm = ProxyConfigORM(
            id=entry.id,
            name=entry.name,
            provider=entry.provider,
            protocol=entry.protocol,
            host=entry.host,
            port=entry.port,
            username=entry.username,
            password=entry.password,
            region=entry.region,
            rotation_type=entry.rotation_type,
            is_active=entry.is_active,
            health_status=entry.health_status,
            fail_count=entry.fail_count,
            success_count=entry.success_count,
            last_check_at=_parse_dt(entry.last_check_at),
            created_at=now,
            updated_at=now,
        )
        db.add(orm)
    else:
        orm.name = entry.name
        orm.provider = entry.provider
        orm.protocol = entry.protocol
        orm.host = entry.host
        orm.port = entry.port
        orm.username = entry.username
        orm.password = entry.password
        orm.region = entry.region
        orm.rotation_type = entry.rotation_type
        orm.is_active = entry.is_active
        orm.health_status = entry.health_status
        orm.fail_count = entry.fail_count
        orm.success_count = entry.success_count
        orm.updated_at = now
        orm.last_check_at = _parse_dt(entry.last_check_at)
    await db.commit()


async def delete_proxy_from_db(db, entry_id: str) -> bool:
    """Delete a proxy entry from the database."""
    from sqlalchemy import select
    from src.models.proxy_config_orm import ProxyConfigORM

    result = await db.execute(select(ProxyConfigORM).where(ProxyConfigORM.id == entry_id))
    orm = result.scalar_one_or_none()
    if orm is None:
        return False
    await db.delete(orm)
    await db.commit()
    return True


async def load_proxies_from_db(db) -> int:
    """Load all proxy entries from DB into memory cache. Returns count loaded."""
    from sqlalchemy import select
    from src.models.proxy_config_orm import ProxyConfigORM
    from datetime import datetime

    result = await db.execute(select(ProxyConfigORM))
    rows = result.scalars().all()

    for row in rows:
        entry = ProxyConfigEntry(
            id=row.id,
            name=row.name,
            provider=row.provider,
            protocol=row.protocol,
            host=row.host,
            port=row.port,
            username=row.username,
            password=row.password,
            region=row.region,
            rotation_type=row.rotation_type,
            is_active=row.is_active,
            health_status=row.health_status,
            fail_count=row.fail_count,
            success_count=row.success_count,
            last_check_at=row.last_check_at.isoformat() if row.last_check_at else None,
            created_at=row.created_at.isoformat() if row.created_at else None,
            updated_at=row.updated_at.isoformat() if row.updated_at else None,
        )
        # Update memory cache directly
        from src.models.proxy_config import _proxy_db
        _proxy_db[row.id] = entry

    return len(rows)


# ─── Helpers ───


def build_requests_proxies(proxy: ProxyConfigEntry) -> Dict[str, str]:
    """Build a requests-compatible proxy dict from a ProxyConfigEntry.

    Returns dict like:
        {"http": "http://user:pass@host:port", "https": "http://user:pass@host:port"}
        or {"http": "socks5://user:pass@host:port", "https": "socks5://user:pass@host:port"}
    """
    protocol = proxy.protocol.lower()
    if protocol not in ("http", "https", "socks5"):
        protocol = "http"

    auth = ""
    if proxy.username:
        auth = f"{proxy.username}"
        if proxy.password:
            auth += f":{proxy.password}"
        auth += "@"

    proxy_url = f"{protocol}://{auth}{proxy.host}:{proxy.port}"

    return {
        "http": proxy_url,
        "https": proxy_url,
    }


def build_requests_proxies_from_dict(data: Dict) -> Dict[str, str]:
    """Build requests-compatible proxy dict from plain dict (used by health-check before save)."""
    protocol = data.get("protocol", "http").lower()
    if protocol not in ("http", "https", "socks5"):
        protocol = "http"

    username = data.get("username", "") or ""
    password = data.get("password", "") or ""
    host = data.get("host", "")
    port = data.get("port", 0)

    auth = ""
    if username:
        auth = f"{username}"
        if password:
            auth += f":{password}"
        auth += "@"

    proxy_url = f"{protocol}://{auth}{host}:{port}"
    return {
        "http": proxy_url,
        "https": proxy_url,
    }


def pick_proxy_for_region(region: str = "") -> Optional[ProxyConfigEntry]:
    """Pick an active proxy for the given region (fallback to any active)."""
    entries = list_proxy_entries(active_only=True)
    if not entries:
        return None

    if region:
        matches = [e for e in entries if e.region.lower() == region.lower()]
        if matches:
            return min(matches, key=lambda e: e.fail_count)

    return min(entries, key=lambda e: e.fail_count)


def record_proxy_result(proxy_id: str, success: bool) -> None:
    """Record success/failure for proxy health tracking."""
    entry = get_proxy_entry(proxy_id)
    if entry is None:
        return
    if success:
        entry.success_count += 1
        entry.fail_count = max(0, entry.fail_count - 1)
        entry.health_status = "healthy"
    else:
        entry.fail_count += 1
        entry.success_count = max(0, entry.success_count - 1)
        if entry.fail_count >= 5:
            entry.health_status = "unhealthy"
            logger.warning("Proxy %s marked unhealthy after %d failures", proxy_id, entry.fail_count)
    entry.last_check_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
    update_proxy_entry(proxy_id, success_count=entry.success_count, fail_count=entry.fail_count,
                       health_status=entry.health_status, last_check_at=entry.last_check_at)
