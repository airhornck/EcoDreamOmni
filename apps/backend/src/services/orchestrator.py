"""Group Orchestrator — W24: account-group autonomy + shard scheduling.

Built on top of matrix_ops + harness/subagent:
  - Each group gets its own plan (Harness Planning Engine)
  - Shard scheduling: stagger tasks across group accounts
  - Autonomy: groups can run independently with their own strategy
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import uuid

from src.services import matrix_ops
from src.harness import planning


@dataclass
class GroupShard:
    shard_id: str
    group_id: str
    account_id: str
    tasks: List[str]
    scheduled_at: Optional[str] = None
    status: str = "pending"


_shards: Dict[str, GroupShard] = {}


def create_group_schedule(
    group_id: str,
    task_template: Dict[str, Any],
    stagger_minutes: int = 15,
) -> List[GroupShard]:
    """Create staggered task shards for all accounts in a group."""
    group = matrix_ops.get_group(group_id)
    if not group:
        raise ValueError(f"Group {group_id} not found")

    from datetime import datetime, timezone, timedelta
    base_time = datetime.now(timezone.utc)
    shards = []

    for i, account_id in enumerate(group.account_ids):
        shard_id = str(uuid.uuid4())[:12]
        scheduled = (base_time + timedelta(minutes=i * stagger_minutes)).isoformat()
        shard = GroupShard(
            shard_id=shard_id,
            group_id=group_id,
            account_id=account_id,
            tasks=[task_template.get("brief_id", "")],
            scheduled_at=scheduled,
            status="scheduled",
        )
        _shards[shard_id] = shard
        shards.append(shard)

    return shards


def get_shard(shard_id: str) -> Optional[GroupShard]:
    return _shards.get(shard_id)


def list_shards(group_id: Optional[str] = None) -> List[GroupShard]:
    items = list(_shards.values())
    if group_id:
        items = [s for s in items if s.group_id == group_id]
    return items


def execute_shard(shard_id: str) -> Dict[str, Any]:
    """Mark a shard as executing/done."""
    shard = _shards.get(shard_id)
    if not shard:
        return {"success": False, "error": "Shard not found"}

    # In production: invoke Publisher/ContentForge via Harness
    shard.status = "done"
    return {"success": True, "shard_id": shard_id, "account_id": shard.account_id}


def group_health_check(group_id: str) -> Dict[str, Any]:
    """Check if a group is healthy enough to run autonomously."""
    group = matrix_ops.get_group(group_id)
    if not group:
        return {"healthy": False, "reason": "Group not found"}

    total = len(group.account_ids)
    if total == 0:
        return {"healthy": False, "reason": "No accounts in group"}

    # Check how many shards are pending/failed
    shards = list_shards(group_id)
    failed = sum(1 for s in shards if s.status == "failed")
    pending = sum(1 for s in shards if s.status == "pending")

    failure_rate = failed / max(len(shards), 1)
    healthy = failure_rate < 0.3 and pending < total * 2

    return {
        "healthy": healthy,
        "group_id": group_id,
        "account_count": total,
        "shards_total": len(shards),
        "shards_failed": failed,
        "shards_pending": pending,
        "failure_rate": round(failure_rate, 2),
    }
