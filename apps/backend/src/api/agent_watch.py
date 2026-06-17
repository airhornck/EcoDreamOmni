"""AgentWatch API — W15–W16.

Routes:
  POST /agent-watch/heartbeat              # Agent heartbeat
  GET  /agent-watch/agents/{id}/status     # Real-time status
  GET  /agent-watch/dashboard              # Full dashboard
  POST /agent-watch/traces                 # Start trace
  POST /agent-watch/traces/{id}/finish     # Finish trace
  POST /agent-watch/traces/{id}/spans      # Record span
  GET  /agent-watch/traces                 # List traces
  GET  /agent-watch/traces/{id}            # Trace detail
  GET  /agent-watch/alerts                 # Alert list
  PATCH /agent-watch/alerts/{id}/ack       # Ack alert
  POST /agent-watch/detect/loop            # Manual loop detection
  POST /agent-watch/detect/timeout         # Manual timeout detection
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.services import agent_watch as aw

router = APIRouter(prefix="/agent-watch", tags=["agent-watch"])


# ─── Schemas ───

class HeartbeatRequest(BaseModel):
    agent_id: str
    status: str = "healthy"
    current_task_id: Optional[str] = None
    queue_depth: int = 0
    memory_mb: Optional[float] = None
    cpu_percent: Optional[float] = None
    version: str = ""


class StartTraceRequest(BaseModel):
    trace_id: str
    content_id: str
    pipeline_type: str = "content_creation"


class RecordSpanRequest(BaseModel):
    span_id: str
    parent_span_id: Optional[str] = None
    agent_id: str
    agent_role: str
    start_time: str
    end_time: Optional[str] = None
    status: str = "ok"
    input_summary: str = ""
    output_summary: str = ""
    token_count: int = 0
    model_version: str = ""
    tool_calls: List[Dict[str, Any]] = []


class DetectLoopRequest(BaseModel):
    agent_id: str
    content_id: str
    window_minutes: int = 5
    threshold: int = 3


class DetectTimeoutRequest(BaseModel):
    agent_id: str
    span_id: str
    max_duration_ms: int = 60000


class AckAlertRequest(BaseModel):
    acked_by: str


class ResolveAlertRequest(BaseModel):
    root_cause: Optional[str] = None


# ─── Heartbeat ───

@router.post("/heartbeat")
def heartbeat(req: HeartbeatRequest):
    hb = aw.record_heartbeat(
        agent_id=req.agent_id,
        status=req.status,
        current_task_id=req.current_task_id,
        queue_depth=req.queue_depth,
        memory_mb=req.memory_mb,
        cpu_percent=req.cpu_percent,
        version=req.version,
    )
    return {
        "agent_id": hb.agent_id,
        "timestamp": hb.timestamp,
        "status": hb.status.value,
        "healthy": aw.is_agent_healthy(req.agent_id),
    }


@router.get("/agents/{agent_id}/status")
def agent_status(agent_id: str):
    return aw.get_agent_status(agent_id)


@router.get("/dashboard")
def dashboard():
    return aw.get_dashboard()


# ─── Trace ───

@router.post("/traces")
def start_trace(req: StartTraceRequest):
    trace = aw.start_trace(req.trace_id, req.content_id, req.pipeline_type)
    return {
        "trace_id": trace.trace_id,
        "content_id": trace.content_id,
        "pipeline_type": trace.pipeline_type,
        "start_time": trace.start_time,
        "status": trace.status.value,
    }


@router.post("/traces/{trace_id}/finish")
def finish_trace(trace_id: str, status: str):
    trace = aw.finish_trace(trace_id, status)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    return {
        "trace_id": trace.trace_id,
        "status": trace.status.value,
        "end_time": trace.end_time,
        "total_tokens": trace.total_tokens,
    }


@router.post("/traces/{trace_id}/spans")
def record_span(trace_id: str, req: RecordSpanRequest):
    span = aw.record_span(
        trace_id=trace_id,
        span_id=req.span_id,
        parent_span_id=req.parent_span_id,
        agent_id=req.agent_id,
        agent_role=req.agent_role,
        start_time=req.start_time,
        end_time=req.end_time,
        status=req.status,
        input_summary=req.input_summary,
        output_summary=req.output_summary,
        token_count=req.token_count,
        model_version=req.model_version,
        tool_calls=req.tool_calls,
    )
    return {
        "span_id": span.span_id,
        "trace_id": span.trace_id,
        "agent_id": span.agent_id,
        "duration_ms": span.duration_ms,
        "status": span.status.value,
    }


@router.get("/traces")
def list_traces(
    content_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
):
    return aw.list_traces(content_id=content_id, status=status, limit=limit)


@router.get("/traces/{trace_id}")
def get_trace(trace_id: str):
    trace = aw.get_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    return trace


# ─── Alerts ───

@router.get("/alerts")
def list_alerts(
    severity: Optional[str] = None,
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
):
    alerts = aw.list_alerts(severity=severity, agent_id=agent_id, status=status, limit=limit)
    return [
        {
            "id": a.id,
            "severity": a.severity.value,
            "alert_type": a.alert_type.value,
            "agent_id": a.agent_id,
            "message": a.message,
            "created_at": a.created_at,
            "status": a.status.value,
        }
        for a in alerts
    ]


@router.patch("/alerts/{alert_id}/ack")
def ack_alert(alert_id: str, req: AckAlertRequest):
    alert = aw.ack_alert(alert_id, req.acked_by)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"alert_id": alert.id, "status": alert.status.value, "acked_by": alert.acked_by}


@router.post("/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: str, req: ResolveAlertRequest):
    alert = aw.resolve_alert(alert_id, req.root_cause)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"alert_id": alert.id, "status": alert.status.value, "root_cause": alert.root_cause}


# ─── Detection (manual trigger or scheduled) ───

@router.post("/detect/loop")
def detect_loop(req: DetectLoopRequest):
    alert = aw.detect_loop(req.agent_id, req.content_id, req.window_minutes, req.threshold)
    if alert:
        return {"alerted": True, "alert_id": alert.id, "message": alert.message}
    return {"alerted": False}


@router.post("/detect/timeout")
def detect_timeout(req: DetectTimeoutRequest):
    alert = aw.detect_timeout(req.agent_id, req.span_id, req.max_duration_ms)
    if alert:
        return {"alerted": True, "alert_id": alert.id, "message": alert.message}
    return {"alerted": False}
