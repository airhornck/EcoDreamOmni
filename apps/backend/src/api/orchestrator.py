"""Orchestrator API — W24.

Routes:
  POST /orchestrator/groups/{gid}/schedule  — Create staggered schedule
  GET  /orchestrator/shards                 — List shards
  POST /orchestrator/shards/{sid}/execute   — Execute shard
  GET  /orchestrator/groups/{gid}/health    — Group health check
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.services import orchestrator as orch

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


class ScheduleRequest(BaseModel):
    brief_id: str
    stagger_minutes: int = 15


@router.post("/groups/{group_id}/schedule")
def schedule_group(group_id: str, req: ScheduleRequest):
    try:
        shards = orch.create_group_schedule(group_id, req.model_dump(), req.stagger_minutes)
        return {
            "group_id": group_id,
            "shards_created": len(shards),
            "shards": [
                {
                    "shard_id": s.shard_id,
                    "account_id": s.account_id,
                    "scheduled_at": s.scheduled_at,
                    "status": s.status,
                }
                for s in shards
            ],
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/shards")
def list_shards(group_id: Optional[str] = None):
    return [
        {
            "shard_id": s.shard_id,
            "group_id": s.group_id,
            "account_id": s.account_id,
            "tasks": s.tasks,
            "scheduled_at": s.scheduled_at,
            "status": s.status,
        }
        for s in orch.list_shards(group_id)
    ]


@router.post("/shards/{shard_id}/execute")
def execute_shard(shard_id: str):
    result = orch.execute_shard(shard_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/groups/{group_id}/health")
def group_health(group_id: str):
    return orch.group_health_check(group_id)
