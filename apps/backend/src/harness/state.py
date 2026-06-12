"""State Graph persistence and checkpointing for Harness.

Aligned with dev-plan H6: "State Graph: persistence and checkpointing".

Each ReAct loop checkpoint stores:
  - Current plan state
  - Tool outputs so far
  - Memory references
  - Verification results

Checkpoints are append-only (tenant-scoped).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid


@dataclass
class Checkpoint:
    checkpoint_id: str
    session_id: str
    agent_id: Optional[str]
    step_number: int
    plan_id: Optional[str]
    tool_outputs: List[Dict[str, Any]] = field(default_factory=list)
    memory_refs: List[str] = field(default_factory=list)
    verification_result: Optional[Dict[str, Any]] = None
    state_data: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""


_checkpoints: Dict[str, List[Checkpoint]] = {}  # session_id → checkpoints


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_checkpoint(
    session_id: str,
    agent_id: Optional[str] = None,
    step_number: int = 0,
    plan_id: Optional[str] = None,
    tool_outputs: Optional[List[Dict[str, Any]]] = None,
    memory_refs: Optional[List[str]] = None,
    verification_result: Optional[Dict[str, Any]] = None,
    state_data: Optional[Dict[str, Any]] = None,
) -> Checkpoint:
    cp = Checkpoint(
        checkpoint_id=str(uuid.uuid4())[:12],
        session_id=session_id,
        agent_id=agent_id,
        step_number=step_number,
        plan_id=plan_id,
        tool_outputs=tool_outputs or [],
        memory_refs=memory_refs or [],
        verification_result=verification_result,
        state_data=state_data or {},
        created_at=_now(),
    )
    if session_id not in _checkpoints:
        _checkpoints[session_id] = []
    _checkpoints[session_id].append(cp)
    return cp


def get_checkpoints(session_id: str, limit: int = 50) -> List[Checkpoint]:
    return _checkpoints.get(session_id, [])[-limit:]


def get_latest_checkpoint(session_id: str) -> Optional[Checkpoint]:
    cps = _checkpoints.get(session_id, [])
    return cps[-1] if cps else None


def rollback_to_checkpoint(session_id: str, checkpoint_id: str) -> Optional[Checkpoint]:
    """Rollback: truncate checkpoints after the given one."""
    cps = _checkpoints.get(session_id, [])
    for i, cp in enumerate(cps):
        if cp.checkpoint_id == checkpoint_id:
            _checkpoints[session_id] = cps[: i + 1]
            return cp
    return None


def list_sessions() -> List[str]:
    return list(_checkpoints.keys())


def session_stats(session_id: str) -> Dict[str, Any]:
    cps = _checkpoints.get(session_id, [])
    return {
        "session_id": session_id,
        "checkpoint_count": len(cps),
        "latest_step": cps[-1].step_number if cps else 0,
        "created_at": cps[0].created_at if cps else None,
        "updated_at": cps[-1].created_at if cps else None,
    }
