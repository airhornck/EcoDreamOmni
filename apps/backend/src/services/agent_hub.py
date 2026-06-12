"""AgentHub — W15: Agent registration, config versioning, lifecycle, permissions.

Aligned with detailed design §5.11 / PRD V2.4 §7.2.
"""

import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class AgentStatus(str, Enum):
    REGISTERED = "registered"
    ACTIVE = "active"
    DEGRADED = "degraded"
    PAUSED = "paused"
    OFFLINE = "offline"


class ConfigStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    ROLLED_BACK = "rolled_back"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class DepType(str, Enum):
    LLM = "llm"
    TOOL = "tool"
    DATA_SOURCE = "data_source"


class DepStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"


@dataclass
class AgentRegistration:
    id: str
    name: str
    role: str
    description: str
    owner: str
    status: AgentStatus = AgentStatus.REGISTERED
    created_at: str = ""
    updated_at: str = ""


@dataclass
class AgentConfigSnapshot:
    id: str
    agent_id: str
    version: int
    env: str  # dev / staging / prod
    config_payload: Dict[str, Any] = field(default_factory=dict)
    # v4.0 P2-4: AI Workbench fields
    ui_config: Dict[str, Any] = field(default_factory=dict)
    quick_actions: List[Dict[str, Any]] = field(default_factory=list)
    adaptive_config: Dict[str, Any] = field(default_factory=dict)
    checksum: str = ""
    created_by: str = ""
    created_at: str = ""
    status: ConfigStatus = ConfigStatus.DRAFT
    approval_status: ApprovalStatus = ApprovalStatus.PENDING


@dataclass
class AgentDependency:
    id: str
    agent_id: str
    dep_type: DepType
    dep_name: str
    dep_status: DepStatus = DepStatus.UNKNOWN
    last_check: Optional[str] = None
    failover_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentPermission:
    id: str
    agent_id: str
    principal: str
    principal_type: str  # USER / SERVICE
    actions: List[str] = field(default_factory=list)
    granted_by: str = ""
    granted_at: str = ""
    expires_at: Optional[str] = None


# ─── In-memory stores ───
_agent_db: Dict[str, AgentRegistration] = {}
_config_db: Dict[str, List[AgentConfigSnapshot]] = {}  # agent_id → configs
_dep_db: Dict[str, List[AgentDependency]] = {}          # agent_id → deps
_perm_db: Dict[str, List[AgentPermission]] = {}         # agent_id → perms
_config_update_callbacks: List[Callable[[str, AgentConfigSnapshot], None]] = []


def on_config_update(callback: Callable[[str, AgentConfigSnapshot], None]) -> None:
    """Register a callback for config hot-reload events."""
    _config_update_callbacks.append(callback)


def _notify_config_update(agent_id: str, config: AgentConfigSnapshot) -> None:
    for cb in _config_update_callbacks:
        try:
            cb(agent_id, config)
        except Exception:
            pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(str(payload).encode()).hexdigest()[:16]


# ─── Agent Registration ───

def register_agent(
    name: str,
    role: str,
    description: str = "",
    owner: str = "",
) -> AgentRegistration:
    agent_id = f"agt_{secrets.token_urlsafe(8)}"
    now = _now()
    agent = AgentRegistration(
        id=agent_id,
        name=name,
        role=role,
        description=description,
        owner=owner,
        status=AgentStatus.REGISTERED,
        created_at=now,
        updated_at=now,
    )
    _agent_db[agent_id] = agent
    _config_db[agent_id] = []
    _dep_db[agent_id] = []
    _perm_db[agent_id] = []
    return agent


def get_agent(agent_id: str) -> Optional[AgentRegistration]:
    return _agent_db.get(agent_id)


def list_agents(
    status: Optional[str] = None,
    role: Optional[str] = None,
    env: Optional[str] = None,
) -> List[AgentRegistration]:
    results = list(_agent_db.values())
    if status:
        results = [a for a in results if a.status.value == status]
    if role:
        results = [a for a in results if a.role == role]
    return results


def update_agent(agent_id: str, **kwargs) -> Optional[AgentRegistration]:
    agent = _agent_db.get(agent_id)
    if not agent:
        return None
    for key, value in kwargs.items():
        if hasattr(agent, key):
            setattr(agent, key, value)
    agent.updated_at = _now()
    return agent


def deregister_agent(agent_id: str) -> bool:
    """Soft delete: mark as offline, retain audit data."""
    agent = _agent_db.get(agent_id)
    if agent:
        agent.status = AgentStatus.OFFLINE
        agent.updated_at = _now()
        return True
    return False


# ─── Config Versioning ───

def create_config(
    agent_id: str,
    env: str,
    config_payload: Dict[str, Any],
    created_by: str = "",
    ui_config: Optional[Dict[str, Any]] = None,
    quick_actions: Optional[List[Dict[str, Any]]] = None,
    adaptive_config: Optional[Dict[str, Any]] = None,
) -> Optional[AgentConfigSnapshot]:
    if agent_id not in _agent_db:
        return None
    configs = _config_db.setdefault(agent_id, [])
    version = len(configs) + 1
    payload = config_payload or {}
    snap = AgentConfigSnapshot(
        id=f"cfg_{secrets.token_urlsafe(6)}",
        agent_id=agent_id,
        version=version,
        env=env,
        config_payload=payload,
        ui_config=ui_config or {},
        quick_actions=quick_actions or [],
        adaptive_config=adaptive_config or {},
        checksum=_sha256(payload),
        created_by=created_by,
        created_at=_now(),
        status=ConfigStatus.DRAFT,
        approval_status=ApprovalStatus.PENDING,
    )
    configs.append(snap)
    return snap


def list_configs(agent_id: str) -> List[AgentConfigSnapshot]:
    return _config_db.get(agent_id, [])[:]


def get_config(agent_id: str, version: int) -> Optional[AgentConfigSnapshot]:
    configs = _config_db.get(agent_id, [])
    for c in configs:
        if c.version == version:
            return c
    return None


def get_active_config(agent_id: str) -> Optional[AgentConfigSnapshot]:
    configs = _config_db.get(agent_id, [])
    for c in reversed(configs):
        if c.status == ConfigStatus.ACTIVE:
            return c
    return None


def activate_config(agent_id: str, version: int) -> Optional[AgentConfigSnapshot]:
    configs = _config_db.get(agent_id, [])
    target = None
    for c in configs:
        if c.version == version:
            target = c
        elif c.status == ConfigStatus.ACTIVE:
            c.status = ConfigStatus.ARCHIVED
    if target:
        target.status = ConfigStatus.ACTIVE
        _notify_config_update(agent_id, target)
        return target
    return None


def rollback_config(agent_id: str, version: int) -> Optional[AgentConfigSnapshot]:
    """Rollback = activate the specified version and archive current."""
    result = activate_config(agent_id, version)
    if result:
        result.status = ConfigStatus.ACTIVE
    return result


# ─── Dependencies ───

def declare_dependency(
    agent_id: str,
    dep_type: str,
    dep_name: str,
    failover_config: Optional[Dict[str, Any]] = None,
) -> Optional[AgentDependency]:
    if agent_id not in _agent_db:
        return None
    dep = AgentDependency(
        id=f"dep_{secrets.token_urlsafe(6)}",
        agent_id=agent_id,
        dep_type=DepType(dep_type),
        dep_name=dep_name,
        dep_status=DepStatus.UNKNOWN,
        last_check=_now(),
        failover_config=failover_config or {},
    )
    _dep_db.setdefault(agent_id, []).append(dep)
    return dep


def list_dependencies(agent_id: str) -> List[AgentDependency]:
    return _dep_db.get(agent_id, [])[:]


def update_dep_status(agent_id: str, dep_name: str, status: str) -> bool:
    deps = _dep_db.get(agent_id, [])
    for d in deps:
        if d.dep_name == dep_name:
            d.dep_status = DepStatus(status)
            d.last_check = _now()
            return True
    return False


def check_all_dependencies(agent_id: str) -> Dict[str, Any]:
    """Health-check all declared dependencies."""
    deps = _dep_db.get(agent_id, [])
    healthy = sum(1 for d in deps if d.dep_status == DepStatus.HEALTHY)
    degraded = sum(1 for d in deps if d.dep_status == DepStatus.DEGRADED)
    down = sum(1 for d in deps if d.dep_status == DepStatus.DOWN)

    # Auto-update agent status if any dep is down
    agent = _agent_db.get(agent_id)
    if agent and down > 0:
        agent.status = AgentStatus.DEGRADED
        agent.updated_at = _now()

    return {
        "agent_id": agent_id,
        "total": len(deps),
        "healthy": healthy,
        "degraded": degraded,
        "down": down,
        "overall": "healthy" if down == 0 and degraded == 0 else "degraded" if down == 0 else "down",
    }


# ─── Permissions ───

def grant_permission(
    agent_id: str,
    principal: str,
    principal_type: str,
    actions: List[str],
    granted_by: str,
    expires_at: Optional[str] = None,
) -> Optional[AgentPermission]:
    if agent_id not in _agent_db:
        return None
    perm = AgentPermission(
        id=f"perm_{secrets.token_urlsafe(6)}",
        agent_id=agent_id,
        principal=principal,
        principal_type=principal_type,
        actions=actions,
        granted_by=granted_by,
        granted_at=_now(),
        expires_at=expires_at,
    )
    _perm_db.setdefault(agent_id, []).append(perm)
    return perm


def list_permissions(agent_id: str) -> List[AgentPermission]:
    return _perm_db.get(agent_id, [])[:]


def check_permission(agent_id: str, principal: str, action: str) -> bool:
    perms = _perm_db.get(agent_id, [])
    for p in perms:
        if p.principal == principal and action in p.actions:
            if p.expires_at is None or p.expires_at > _now():
                return True
    return False


def revoke_permission(agent_id: str, perm_id: str) -> bool:
    perms = _perm_db.get(agent_id, [])
    for i, p in enumerate(perms):
        if p.id == perm_id:
            perms.pop(i)
            return True
    return False


# ─── AI Workbench Config ───

def get_workbench_config(agent_id: str) -> Optional[Dict[str, Any]]:
    """Return workbench-ready config for AI Workbench display."""
    agent = _agent_db.get(agent_id)
    if not agent:
        return None
    active = get_active_config(agent_id)
    if not active:
        return None
    return {
        "agent_id": agent_id,
        "agent_name": agent.name,
        "agent_role": agent.role,
        "config_version": active.version,
        "env": active.env,
        "ui_config": active.ui_config,
        "quick_actions": active.quick_actions,
        "adaptive_config": active.adaptive_config,
        "status": agent.status.value,
    }
