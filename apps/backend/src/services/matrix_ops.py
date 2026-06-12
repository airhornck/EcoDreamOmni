"""Matrix Operations — W21: scaling brief distribution + account grouping.

Features:
  - Account grouping by lifecycle, city, persona, vertical
  - Brief batch assignment to groups
  - Batch publish scheduling
  - Group health overview
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import uuid


@dataclass
class AccountGroup:
    group_id: str
    name: str
    criteria: Dict[str, Any]  # e.g. {"lifecycle_phase": "growth", "city": "Shanghai"}
    account_ids: List[str]
    created_at: str


@dataclass
class BriefAssignment:
    assignment_id: str
    brief_id: str
    group_id: str
    account_ids: List[str]
    status: str  # pending | assigned | completed
    assigned_at: str


@dataclass
class BatchSchedule:
    schedule_id: str
    task_ids: List[str]
    group_id: str
    stagger_minutes: int
    status: str


_groups: Dict[str, AccountGroup] = {}
_assignments: Dict[str, BriefAssignment] = {}
_schedules: Dict[str, BatchSchedule] = {}


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


# ─── Account Grouping ───

def create_group(
    name: str,
    criteria: Dict[str, Any],
    account_ids: List[str],
) -> AccountGroup:
    group_id = str(uuid.uuid4())[:12]
    group = AccountGroup(
        group_id=group_id,
        name=name,
        criteria=criteria,
        account_ids=account_ids,
        created_at=_now(),
    )
    _groups[group_id] = group
    return group


def get_group(group_id: str) -> Optional[AccountGroup]:
    return _groups.get(group_id)


def list_groups() -> List[AccountGroup]:
    return list(_groups.values())


def delete_group(group_id: str) -> bool:
    return _groups.pop(group_id, None) is not None


def auto_group_accounts(accounts: List[Dict[str, Any]]) -> List[AccountGroup]:
    """Auto-create groups by lifecycle_phase + city."""
    buckets: Dict[tuple, List[str]] = {}
    for acc in accounts:
        key = (acc.get("lifecycle_phase", "unknown"), acc.get("city", "unknown"))
        buckets.setdefault(key, []).append(acc["id"])

    created = []
    for (phase, city), ids in buckets.items():
        if len(ids) >= 2:
            group = create_group(
                name=f"{phase}_{city}",
                criteria={"lifecycle_phase": phase, "city": city},
                account_ids=ids,
            )
            created.append(group)
    return created


# ─── Brief Batch Assignment ───

def assign_brief_to_group(
    brief_id: str,
    group_id: str,
) -> BriefAssignment:
    group = _groups.get(group_id)
    if not group:
        raise ValueError(f"Group {group_id} not found")

    assignment_id = str(uuid.uuid4())[:12]
    assignment = BriefAssignment(
        assignment_id=assignment_id,
        brief_id=brief_id,
        group_id=group_id,
        account_ids=group.account_ids.copy(),
        status="pending",
        assigned_at=_now(),
    )
    _assignments[assignment_id] = assignment
    return assignment


def get_assignment(assignment_id: str) -> Optional[BriefAssignment]:
    return _assignments.get(assignment_id)


def list_assignments(group_id: Optional[str] = None) -> List[BriefAssignment]:
    items = list(_assignments.values())
    if group_id:
        items = [a for a in items if a.group_id == group_id]
    return items


def update_assignment_status(assignment_id: str, status: str) -> bool:
    a = _assignments.get(assignment_id)
    if a:
        a.status = status
        return True
    return False


# ─── Batch Scheduling ───

def create_batch_schedule(
    group_id: str,
    task_ids: List[str],
    stagger_minutes: int = 15,
) -> BatchSchedule:
    schedule_id = str(uuid.uuid4())[:12]
    schedule = BatchSchedule(
        schedule_id=schedule_id,
        task_ids=task_ids,
        group_id=group_id,
        stagger_minutes=stagger_minutes,
        status="pending",
    )
    _schedules[schedule_id] = schedule
    return schedule


def get_batch_schedule(schedule_id: str) -> Optional[BatchSchedule]:
    return _schedules.get(schedule_id)


def list_batch_schedules(group_id: Optional[str] = None) -> List[BatchSchedule]:
    items = list(_schedules.values())
    if group_id:
        items = [s for s in items if s.group_id == group_id]
    return items


# ─── Group Health Overview ───

def group_health_overview(group_id: str, account_healths: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate health metrics for a group."""
    group = _groups.get(group_id)
    if not group:
        return {"error": "Group not found"}

    healths = [account_healths.get(aid, {}) for aid in group.account_ids]
    scores = [h.get("health_score", 0) for h in healths if h]
    statuses = [h.get("status", "unknown") for h in healths if h]

    return {
        "group_id": group_id,
        "account_count": len(group.account_ids),
        "avg_health_score": round(sum(scores) / len(scores), 2) if scores else 0,
        "active_count": statuses.count("active"),
        "warming_count": statuses.count("warming"),
        "blocked_count": statuses.count("blocked"),
        "criteria": group.criteria,
    }
