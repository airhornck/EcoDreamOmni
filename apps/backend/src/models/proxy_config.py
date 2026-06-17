"""Proxy configuration models and in-memory store."""

import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class ProxyConfigEntry:
    """A proxy server configuration entry."""

    id: str
    name: str
    provider: str  # brightdata, oxylabs, custom, etc.
    protocol: str  # http, https, socks5
    host: str
    port: int
    username: str = ""
    password: str = ""
    region: str = ""  # e.g. "us", "cn", "jp"
    rotation_type: str = "static"  # static, session, rotating
    is_active: bool = True
    health_status: str = "unknown"  # healthy, unhealthy, unknown
    last_check_at: Optional[str] = None
    fail_count: int = 0
    success_count: int = 0
    created_at: str = ""
    updated_at: str = ""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


_proxy_db: Dict[str, ProxyConfigEntry] = {}


def create_proxy_entry(
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
    entry_id = secrets.token_urlsafe(16)
    now = _now()
    entry = ProxyConfigEntry(
        id=entry_id,
        name=name,
        provider=provider,
        protocol=protocol,
        host=host,
        port=port,
        username=username,
        password=password,
        region=region,
        rotation_type=rotation_type,
        is_active=True,
        health_status="unknown",
        created_at=now,
        updated_at=now,
    )
    _proxy_db[entry_id] = entry
    return entry


def get_proxy_entry(entry_id: str) -> Optional[ProxyConfigEntry]:
    return _proxy_db.get(entry_id)


def list_proxy_entries(active_only: bool = False) -> List[ProxyConfigEntry]:
    entries = list(_proxy_db.values())
    if active_only:
        entries = [e for e in entries if e.is_active]
    return entries


def update_proxy_entry(entry_id: str, **kwargs) -> Optional[ProxyConfigEntry]:
    entry = _proxy_db.get(entry_id)
    if entry is None:
        return None
    for key, value in kwargs.items():
        if hasattr(entry, key):
            setattr(entry, key, value)
    entry.updated_at = _now()
    return entry


def delete_proxy_entry(entry_id: str) -> bool:
    if entry_id in _proxy_db:
        del _proxy_db[entry_id]
        return True
    return False


def clear_proxy_entries() -> None:
    _proxy_db.clear()
