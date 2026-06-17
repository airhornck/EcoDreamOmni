"""Audit API — W27.

Routes:
  GET /audit/logs        — Query audit logs
  GET /audit/logs/{id}   — Get single log
  GET /audit/stats       — Audit statistics
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from src.services import audit_logger

router = APIRouter(prefix="/audit", tags=["audit"])


class LogEventRequest(BaseModel):
    tenant_id: str
    actor_id: str
    actor_type: str = "user"
    event_type: str
    resource_type: str
    resource_id: str
    action: str
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None


@router.get("/logs")
def query_logs(
    tenant_id: Optional[str] = None,
    event_type: Optional[str] = None,
    actor_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    logs = audit_logger.query_logs(
        tenant_id=tenant_id,
        event_type=event_type,
        actor_id=actor_id,
        resource_type=resource_type,
        limit=limit,
        offset=offset,
    )
    return {
        "total": audit_logger.count_logs(tenant_id),
        "limit": limit,
        "offset": offset,
        "logs": [
            {
                "log_id": log.log_id,
                "tenant_id": log.tenant_id,
                "actor_id": log.actor_id,
                "event_type": log.event_type,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "action": log.action,
                "timestamp": log.timestamp,
            }
            for log in logs
        ],
    }


@router.post("/logs")
def log_event(req: LogEventRequest):
    entry = audit_logger.log_event(
        tenant_id=req.tenant_id,
        actor_id=req.actor_id,
        actor_type=req.actor_type,
        event_type=req.event_type,
        resource_type=req.resource_type,
        resource_id=req.resource_id,
        action=req.action,
        before_state=req.before_state,
        after_state=req.after_state,
    )
    return {"log_id": entry.log_id, "timestamp": entry.timestamp}


@router.get("/stats")
def audit_stats():
    total = audit_logger.count_logs()
    return {
        "total_logs": total,
        "event_types": {},  # MVP placeholder
    }
