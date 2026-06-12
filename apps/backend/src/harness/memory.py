"""3-tier memory manager for Agent Harness.

Aligned with dev-plan H2: "Memory Manager: short-term / working / long-term".

Constraints (per PRD):
  - Long-term memory is **tenant-scoped only** (no cross-tenant federation).
  - Compliance audit data retained >= 2 years (Phase 2+).
  - Short-term is session-local (in-memory).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class MemoryEntry:
    key: str
    value: str
    role: str  # user, assistant, system, tool
    timestamp: str
    ttl_seconds: Optional[int] = None


# ─── Short-Term Memory (session-local) ───
_short_term: Dict[str, List[MemoryEntry]] = {}  # session_id → entries


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def short_term_put(session_id: str, key: str, value: str, role: str = "system") -> None:
    if session_id not in _short_term:
        _short_term[session_id] = []
    _short_term[session_id].append(MemoryEntry(key=key, value=value, role=role, timestamp=_now()))


def short_term_get(session_id: str, limit: int = 10) -> List[MemoryEntry]:
    entries = _short_term.get(session_id, [])
    return entries[-limit:]


def short_term_clear(session_id: str) -> None:
    _short_term.pop(session_id, None)


# ─── Working Memory (pipeline-level summaries) ───
_working: Dict[str, Dict[str, Any]] = {}  # pipeline_id → summary


def working_put(pipeline_id: str, summary: Dict[str, Any]) -> None:
    """Store a pipeline-level working memory summary."""
    _working[pipeline_id] = {
        "summary": summary,
        "updated_at": _now(),
    }


def working_get(pipeline_id: str) -> Optional[Dict[str, Any]]:
    entry = _working.get(pipeline_id)
    return entry["summary"] if entry else None


# ─── Long-Term Memory (tenant-scoped, append-only) ───
_long_term: Dict[str, List[Dict[str, Any]]] = {}  # tenant_id → records


def long_term_append(tenant_id: str, record: Dict[str, Any]) -> None:
    """Append an immutable record to long-term memory."""
    if tenant_id not in _long_term:
        _long_term[tenant_id] = []
    record["_stored_at"] = _now()
    _long_term[tenant_id].append(record)


def long_term_query(tenant_id: str, tag: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Query long-term memory records."""
    records = _long_term.get(tenant_id, [])
    if tag:
        records = [r for r in records if tag in r.get("tags", [])]
    return records[-limit:]


def long_term_count(tenant_id: str) -> int:
    return len(_long_term.get(tenant_id, []))
