"""Audit Logger — W27: security audit trail.

Features:
  - Append-only audit log entries
  - Tenant-scoped queries
  - Event types: login, content_publish, config_change, rule_violation, api_key_usage
  - Immutable: no updates, no deletes
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid


@dataclass
class AuditLogEntry:
    log_id: str
    tenant_id: str
    actor_id: str
    actor_type: str  # user | api_key | system
    event_type: str
    resource_type: str
    resource_id: str
    action: str
    before_state: Optional[Dict[str, Any]]
    after_state: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    timestamp: str


_audit_db: List[AuditLogEntry] = []


def log_event(
    tenant_id: str,
    actor_id: str,
    actor_type: str,
    event_type: str,
    resource_type: str,
    resource_id: str,
    action: str,
    before_state: Optional[Dict[str, Any]] = None,
    after_state: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLogEntry:
    """Append an immutable audit log entry."""
    entry = AuditLogEntry(
        log_id=f"aud_{uuid.uuid4().hex[:16]}",
        tenant_id=tenant_id,
        actor_id=actor_id,
        actor_type=actor_type,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        before_state=before_state,
        after_state=after_state,
        ip_address=ip_address,
        user_agent=user_agent,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    _audit_db.append(entry)
    return entry


def query_logs(
    tenant_id: Optional[str] = None,
    event_type: Optional[str] = None,
    actor_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[AuditLogEntry]:
    """Query audit logs with filters. Append-only, no delete."""
    results = _audit_db[:]

    if tenant_id:
        results = [e for e in results if e.tenant_id == tenant_id]
    if event_type:
        results = [e for e in results if e.event_type == event_type]
    if actor_id:
        results = [e for e in results if e.actor_id == actor_id]
    if resource_type:
        results = [e for e in results if e.resource_type == resource_type]
    if start_time:
        results = [e for e in results if e.timestamp >= start_time]
    if end_time:
        results = [e for e in results if e.timestamp <= end_time]

    # Sort by timestamp desc, then paginate
    results.sort(key=lambda e: e.timestamp, reverse=True)
    return results[offset:offset + limit]


def count_logs(tenant_id: Optional[str] = None) -> int:
    if tenant_id:
        return sum(1 for e in _audit_db if e.tenant_id == tenant_id)
    return len(_audit_db)
