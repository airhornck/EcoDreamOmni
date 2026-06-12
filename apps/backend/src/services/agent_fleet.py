"""Agent Fleet — v4.0 Phase 8 P8-3.

Agent 舰队管理：同类 Agent 多实例池、负载均衡、健康检查。
MVP: 内存实例池，无持久化（Phase 2 可接入 DB）。

架构红线:
- §2.1 Agent 禁 DB: Fleet 管理元数据，不直接执行业务 SQL
- §2.2 Event Bus 优先: 实例状态变更通过 Event Bus 广播
- §2.4 租户隔离: Fleet 操作必须带 tenant_id
"""

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional



class InstanceStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    BUSY = "busy"


class RoutingStrategy(str, Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_LOAD = "least_load"
    CAPABILITY_MATCH = "capability_match"


@dataclass
class AgentInstance:
    """单个 Agent 实例."""

    instance_id: str
    agent_type: str
    agent_id: str
    status: InstanceStatus = InstanceStatus.HEALTHY
    tenant_id: str = ""
    capabilities: List[str] = field(default_factory=list)
    current_tasks: int = 0
    max_tasks: int = 5
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    last_heartbeat_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.last_heartbeat_at:
            self.last_heartbeat_at = self.created_at

    @property
    def is_available(self) -> bool:
        return self.status == InstanceStatus.HEALTHY and self.current_tasks < self.max_tasks

    @property
    def load_ratio(self) -> float:
        return self.current_tasks / max(self.max_tasks, 1)


@dataclass
class FleetHealth:
    """舰队健康快照."""

    total_instances: int = 0
    healthy_count: int = 0
    degraded_count: int = 0
    offline_count: int = 0
    busy_count: int = 0
    avg_cpu_percent: float = 0.0
    avg_memory_percent: float = 0.0
    total_queue_depth: int = 0
    updated_at: str = ""


@dataclass
class AgentFleet:
    """Agent 舰队定义."""

    fleet_id: str
    agent_type: str
    tenant_id: str = ""
    instances: List[AgentInstance] = field(default_factory=list)
    min_instances: int = 1
    max_instances: int = 10
    routing_strategy: RoutingStrategy = RoutingStrategy.ROUND_ROBIN
    auto_scale_enabled: bool = False
    scale_up_cpu_threshold: float = 70.0
    scale_up_queue_depth: int = 10
    scale_down_idle_duration_sec: int = 300
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    @property
    def health(self) -> FleetHealth:
        total = len(self.instances)
        healthy = sum(1 for i in self.instances if i.status == InstanceStatus.HEALTHY)
        degraded = sum(1 for i in self.instances if i.status == InstanceStatus.DEGRADED)
        offline = sum(1 for i in self.instances if i.status == InstanceStatus.OFFLINE)
        busy = sum(1 for i in self.instances if i.status == InstanceStatus.BUSY)
        cpus = [i.cpu_percent for i in self.instances if i.status != InstanceStatus.OFFLINE]
        mems = [i.memory_percent for i in self.instances if i.status != InstanceStatus.OFFLINE]
        queue = sum(i.current_tasks for i in self.instances)
        return FleetHealth(
            total_instances=total,
            healthy_count=healthy,
            degraded_count=degraded,
            offline_count=offline,
            busy_count=busy,
            avg_cpu_percent=sum(cpus) / max(len(cpus), 1),
            avg_memory_percent=sum(mems) / max(len(mems), 1),
            total_queue_depth=queue,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )


# ─── In-memory fleet registry ───
_fleet_db: Dict[str, AgentFleet] = {}
_fleet_counter: Dict[str, int] = {}  # {fleet_id: round_robin_index}


def _new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(8)}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ═══════════════════════════════════════════════════════
# Fleet Management API
# ═══════════════════════════════════════════════════════


def create_fleet(
    agent_type: str,
    tenant_id: str,
    min_instances: int = 1,
    max_instances: int = 10,
    routing_strategy: str = "round_robin",
    auto_scale_enabled: bool = False,
) -> AgentFleet:
    fleet_id = _new_id("fleet")
    fleet = AgentFleet(
        fleet_id=fleet_id,
        agent_type=agent_type,
        tenant_id=tenant_id,
        min_instances=min_instances,
        max_instances=max_instances,
        routing_strategy=RoutingStrategy(routing_strategy),
        auto_scale_enabled=auto_scale_enabled,
    )
    _fleet_db[fleet_id] = fleet
    return fleet


def get_fleet(fleet_id: str) -> Optional[AgentFleet]:
    return _fleet_db.get(fleet_id)


def list_fleets(tenant_id: str = "") -> List[AgentFleet]:
    if tenant_id:
        return [f for f in _fleet_db.values() if f.tenant_id == tenant_id]
    return list(_fleet_db.values())


def delete_fleet(fleet_id: str) -> bool:
    if fleet_id in _fleet_db:
        del _fleet_db[fleet_id]
        _fleet_counter.pop(fleet_id, None)
        return True
    return False


# ═══════════════════════════════════════════════════════
# Instance Management
# ═══════════════════════════════════════════════════════


def register_instance(
    fleet_id: str,
    agent_id: str,
    capabilities: Optional[List[str]] = None,
    max_tasks: int = 5,
    metadata: Optional[Dict[str, Any]] = None,
) -> Optional[AgentInstance]:
    fleet = _fleet_db.get(fleet_id)
    if not fleet:
        return None

    if len(fleet.instances) >= fleet.max_instances:
        raise ValueError(f"Fleet {fleet_id} 已达最大实例数 {fleet.max_instances}")

    instance = AgentInstance(
        instance_id=_new_id("inst"),
        agent_type=fleet.agent_type,
        agent_id=agent_id,
        tenant_id=fleet.tenant_id,
        capabilities=capabilities or [],
        max_tasks=max_tasks,
        metadata=metadata or {},
    )
    fleet.instances.append(instance)
    return instance


def unregister_instance(fleet_id: str, instance_id: str) -> bool:
    fleet = _fleet_db.get(fleet_id)
    if not fleet:
        return False
    original_len = len(fleet.instances)
    fleet.instances = [i for i in fleet.instances if i.instance_id != instance_id]
    return len(fleet.instances) < original_len


def get_instance(fleet_id: str, instance_id: str) -> Optional[AgentInstance]:
    fleet = _fleet_db.get(fleet_id)
    if not fleet:
        return None
    for inst in fleet.instances:
        if inst.instance_id == instance_id:
            return inst
    return None


def heartbeat(
    fleet_id: str,
    instance_id: str,
    cpu_percent: float = 0.0,
    memory_percent: float = 0.0,
    current_tasks: int = 0,
    status: Optional[str] = None,
) -> bool:
    instance = get_instance(fleet_id, instance_id)
    if not instance:
        return False

    instance.last_heartbeat_at = _now()
    instance.cpu_percent = cpu_percent
    instance.memory_percent = memory_percent
    instance.current_tasks = current_tasks
    if status:
        instance.status = InstanceStatus(status)
    return True


# ═══════════════════════════════════════════════════════
# Routing
# ═══════════════════════════════════════════════════════


def route_task(
    fleet_id: str,
    required_capabilities: Optional[List[str]] = None,
) -> Optional[AgentInstance]:
    """Route a task to an available instance according to fleet strategy."""
    fleet = _fleet_db.get(fleet_id)
    if not fleet:
        return None

    available = [
        i for i in fleet.instances
        if i.is_available and (not required_capabilities or all(c in i.capabilities for c in required_capabilities))
    ]
    if not available:
        return None

    strategy = fleet.routing_strategy

    if strategy == RoutingStrategy.ROUND_ROBIN:
        idx = _fleet_counter.get(fleet_id, 0) % max(len(available), 1)
        _fleet_counter[fleet_id] = idx + 1
        return available[idx]

    if strategy == RoutingStrategy.LEAST_LOAD:
        return min(available, key=lambda i: i.load_ratio)

    if strategy == RoutingStrategy.CAPABILITY_MATCH:
        # Score by capability match count, then by load
        scored = []
        for inst in available:
            score = 0
            if required_capabilities:
                score = sum(1 for c in required_capabilities if c in inst.capabilities)
            scored.append((score, inst.load_ratio, inst))
        scored.sort(key=lambda x: (-x[0], x[1]))
        return scored[0][2]

    # Default round robin
    idx = _fleet_counter.get(fleet_id, 0) % max(len(available), 1)
    _fleet_counter[fleet_id] = idx + 1
    return available[idx]


# ═══════════════════════════════════════════════════════
# Auto-scaling (MVP: evaluation only, no actual scaling)
# ═══════════════════════════════════════════════════════


def evaluate_scaling(fleet_id: str) -> Dict[str, Any]:
    """Evaluate whether fleet should scale up/down. Returns recommendation only."""
    fleet = _fleet_db.get(fleet_id)
    if not fleet:
        return {"error": "Fleet not found"}

    health = fleet.health
    recommendation = "maintain"
    reason = "负载正常"

    if not fleet.auto_scale_enabled:
        recommendation = "manual"
        reason = "自动伸缩未启用"
    else:
        if health.avg_cpu_percent > fleet.scale_up_cpu_threshold:
            recommendation = "scale_up"
            reason = f"CPU {health.avg_cpu_percent:.1f}% 超过阈值 {fleet.scale_up_cpu_threshold}%"
        elif health.total_queue_depth > fleet.scale_up_queue_depth:
            recommendation = "scale_up"
            reason = f"队列深度 {health.total_queue_depth} 超过阈值 {fleet.scale_up_queue_depth}"
        elif health.healthy_count > fleet.min_instances and health.total_queue_depth == 0:
            # Check idle duration (MVP: simplified, always recommend scale down if idle)
            recommendation = "scale_down"
            reason = f"实例数 {health.healthy_count} > 最小 {fleet.min_instances} 且队列空闲"

    return {
        "fleet_id": fleet_id,
        "recommendation": recommendation,
        "reason": reason,
        "current_health": {
            "total_instances": health.total_instances,
            "healthy_count": health.healthy_count,
            "avg_cpu_percent": round(health.avg_cpu_percent, 2),
            "total_queue_depth": health.total_queue_depth,
        },
        "limits": {
            "min_instances": fleet.min_instances,
            "max_instances": fleet.max_instances,
            "scale_up_cpu_threshold": fleet.scale_up_cpu_threshold,
            "scale_up_queue_depth": fleet.scale_up_queue_depth,
        },
    }


# ═══════════════════════════════════════════════════════
# Fleet-wide Operations
# ═══════════════════════════════════════════════════════


def list_instances(fleet_id: str, status_filter: Optional[str] = None) -> List[AgentInstance]:
    fleet = _fleet_db.get(fleet_id)
    if not fleet:
        return []
    if status_filter:
        return [i for i in fleet.instances if i.status.value == status_filter]
    return list(fleet.instances)


def update_instance_status(fleet_id: str, instance_id: str, new_status: str) -> bool:
    instance = get_instance(fleet_id, instance_id)
    if not instance:
        return False
    instance.status = InstanceStatus(new_status)
    return True


def get_fleet_health(fleet_id: str) -> Optional[Dict[str, Any]]:
    fleet = _fleet_db.get(fleet_id)
    if not fleet:
        return None
    h = fleet.health
    return {
        "fleet_id": fleet_id,
        "agent_type": fleet.agent_type,
        "total_instances": h.total_instances,
        "healthy_count": h.healthy_count,
        "degraded_count": h.degraded_count,
        "offline_count": h.offline_count,
        "busy_count": h.busy_count,
        "avg_cpu_percent": round(h.avg_cpu_percent, 2),
        "avg_memory_percent": round(h.avg_memory_percent, 2),
        "total_queue_depth": h.total_queue_depth,
        "routing_strategy": fleet.routing_strategy.value,
        "updated_at": h.updated_at,
    }
