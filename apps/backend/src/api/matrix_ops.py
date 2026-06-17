"""Matrix Operations API — W21.

Routes:
  POST /matrix/groups              — Create account group
  GET  /matrix/groups              — List groups
  GET  /matrix/groups/{gid}        — Get group detail
  DELETE /matrix/groups/{gid}      — Delete group
  POST /matrix/groups/auto         — Auto-group accounts
  POST /matrix/assignments         — Assign brief to group
  GET  /matrix/assignments         — List assignments
  POST /matrix/schedules           — Create batch schedule
  GET  /matrix/schedules           — List schedules
  GET  /matrix/groups/{gid}/health — Group health overview
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.services import matrix_ops

router = APIRouter(prefix="/matrix", tags=["matrix-ops"])


# ─── Schemas ───

class CreateGroupRequest(BaseModel):
    name: str
    criteria: Dict[str, Any] = {}
    account_ids: List[str]


class AutoGroupRequest(BaseModel):
    accounts: List[Dict[str, Any]]


class AssignBriefRequest(BaseModel):
    brief_id: str
    group_id: str


class CreateScheduleRequest(BaseModel):
    group_id: str
    task_ids: List[str]
    stagger_minutes: int = 15


class HealthOverviewRequest(BaseModel):
    account_healths: Dict[str, Dict[str, Any]] = {}


# ─── Groups ───

@router.post("/groups", status_code=201)
def create_group(req: CreateGroupRequest):
    group = matrix_ops.create_group(
        name=req.name,
        criteria=req.criteria,
        account_ids=req.account_ids,
    )
    return {
        "group_id": group.group_id,
        "name": group.name,
        "criteria": group.criteria,
        "account_count": len(group.account_ids),
        "created_at": group.created_at,
    }


@router.get("/groups")
def list_groups():
    return [
        {
            "group_id": g.group_id,
            "name": g.name,
            "criteria": g.criteria,
            "account_count": len(g.account_ids),
        }
        for g in matrix_ops.list_groups()
    ]


@router.get("/groups/{group_id}")
def get_group(group_id: str):
    g = matrix_ops.get_group(group_id)
    if not g:
        raise HTTPException(status_code=404, detail="Group not found")
    return {
        "group_id": g.group_id,
        "name": g.name,
        "criteria": g.criteria,
        "account_ids": g.account_ids,
        "created_at": g.created_at,
    }


@router.delete("/groups/{group_id}", status_code=204)
def delete_group(group_id: str):
    ok = matrix_ops.delete_group(group_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Group not found")
    return None


@router.post("/groups/auto")
def auto_group(req: AutoGroupRequest):
    groups = matrix_ops.auto_group_accounts(req.accounts)
    return {
        "groups_created": len(groups),
        "groups": [
            {
                "group_id": g.group_id,
                "name": g.name,
                "criteria": g.criteria,
                "account_count": len(g.account_ids),
            }
            for g in groups
        ],
    }


# ─── Assignments ───

@router.post("/assignments", status_code=201)
def assign_brief(req: AssignBriefRequest):
    try:
        a = matrix_ops.assign_brief_to_group(req.brief_id, req.group_id)
        return {
            "assignment_id": a.assignment_id,
            "brief_id": a.brief_id,
            "group_id": a.group_id,
            "account_count": len(a.account_ids),
            "status": a.status,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/assignments")
def list_assignments(group_id: Optional[str] = None):
    return [
        {
            "assignment_id": a.assignment_id,
            "brief_id": a.brief_id,
            "group_id": a.group_id,
            "account_count": len(a.account_ids),
            "status": a.status,
        }
        for a in matrix_ops.list_assignments(group_id)
    ]


# ─── Schedules ───

@router.post("/schedules", status_code=201)
def create_schedule(req: CreateScheduleRequest):
    s = matrix_ops.create_batch_schedule(
        group_id=req.group_id,
        task_ids=req.task_ids,
        stagger_minutes=req.stagger_minutes,
    )
    return {
        "schedule_id": s.schedule_id,
        "group_id": s.group_id,
        "task_count": len(s.task_ids),
        "stagger_minutes": s.stagger_minutes,
        "status": s.status,
    }


@router.get("/schedules")
def list_schedules(group_id: Optional[str] = None):
    return [
        {
            "schedule_id": s.schedule_id,
            "group_id": s.group_id,
            "task_count": len(s.task_ids),
            "stagger_minutes": s.stagger_minutes,
            "status": s.status,
        }
        for s in matrix_ops.list_batch_schedules(group_id)
    ]


# ─── Health ───

@router.get("/groups/{group_id}/health")
def group_health(group_id: str, req: HealthOverviewRequest):
    g = matrix_ops.get_group(group_id)
    if not g:
        raise HTTPException(status_code=404, detail="Group not found")
    return matrix_ops.group_health_overview(group_id, req.account_healths)
