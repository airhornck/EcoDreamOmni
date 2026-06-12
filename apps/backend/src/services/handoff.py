"""Handoff Protocol — v4.0 Phase 9.

Agent 间交接协议：状态传递、上下文继承、责任转移。
MVP: 内存消息格式 + 基础路由，无持久化。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class HandoffType(str, Enum):
    DELEGATE = "delegate"       # 完全委托
    COLLABORATE = "collaborate" # 协作（共同完成）
    ESCALATE = "escalate"       # 升级（上报）
    RETURN = "return"           # 返回结果给上级


class HandoffStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMPLETED = "completed"
    EXPIRED = "expired"


@dataclass
class HandoffMessage:
    """Handoff 消息格式 — Agent 间状态交接的标准信封."""
    handoff_id: str
    handoff_type: HandoffType
    from_agent_id: str
    to_agent_id: str
    execution_id: str
    tenant_id: str = ""

    # 上下文传递
    context_payload: Dict[str, Any] = field(default_factory=dict)
    checkpoint_ref: str = ""  # Checkpoint ID，用于断点续跑

    # 交接内容
    task_description: str = ""
    deliverables: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)

    # 状态
    status: HandoffStatus = HandoffStatus.PENDING
    created_at: str = ""
    expires_at: str = ""
    completed_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.expires_at:
            # Default expiry: 5 minutes
            expiry = datetime.now(timezone.utc) + __import__("datetime").timedelta(minutes=5)
            self.expires_at = expiry.isoformat()


# ─── In-memory handoff registry ───
_handoff_db: Dict[str, HandoffMessage] = {}


def _new_id() -> str:
    import secrets
    return f"handoff_{secrets.token_urlsafe(8)}"


def create_handoff(
    handoff_type: str,
    from_agent_id: str,
    to_agent_id: str,
    execution_id: str,
    tenant_id: str = "",
    context_payload: Optional[Dict[str, Any]] = None,
    task_description: str = "",
    deliverables: Optional[List[str]] = None,
    constraints: Optional[List[str]] = None,
) -> HandoffMessage:
    """Create a new handoff message."""
    msg = HandoffMessage(
        handoff_id=_new_id(),
        handoff_type=HandoffType(handoff_type),
        from_agent_id=from_agent_id,
        to_agent_id=to_agent_id,
        execution_id=execution_id,
        tenant_id=tenant_id,
        context_payload=context_payload or {},
        task_description=task_description,
        deliverables=deliverables or [],
        constraints=constraints or [],
    )
    _handoff_db[msg.handoff_id] = msg
    return msg


def get_handoff(handoff_id: str) -> Optional[HandoffMessage]:
    return _handoff_db.get(handoff_id)


def accept_handoff(handoff_id: str) -> bool:
    msg = _handoff_db.get(handoff_id)
    if not msg or msg.status != HandoffStatus.PENDING:
        return False
    msg.status = HandoffStatus.ACCEPTED
    return True


def reject_handoff(handoff_id: str, reason: str = "") -> bool:
    msg = _handoff_db.get(handoff_id)
    if not msg or msg.status != HandoffStatus.PENDING:
        return False
    msg.status = HandoffStatus.REJECTED
    if reason:
        msg.context_payload["rejection_reason"] = reason
    return True


def complete_handoff(handoff_id: str, result_payload: Optional[Dict[str, Any]] = None) -> bool:
    msg = _handoff_db.get(handoff_id)
    if not msg or msg.status != HandoffStatus.ACCEPTED:
        return False
    msg.status = HandoffStatus.COMPLETED
    msg.completed_at = datetime.now(timezone.utc).isoformat()
    if result_payload:
        msg.context_payload["result"] = result_payload
    return True


def list_pending_handoffs(agent_id: str) -> List[HandoffMessage]:
    """List all pending handoffs targeting an agent."""
    return [
        msg for msg in _handoff_db.values()
        if msg.to_agent_id == agent_id and msg.status == HandoffStatus.PENDING
    ]


def list_handoffs_by_execution(execution_id: str) -> List[HandoffMessage]:
    return [msg for msg in _handoff_db.values() if msg.execution_id == execution_id]
