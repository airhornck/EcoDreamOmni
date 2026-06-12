"""AgentWatch — W15–W16: heartbeat, status dashboard, trace, anomaly detection, alerts.

Aligned with detailed design §5.12 / PRD V2.4 §7.3.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
import secrets
import uuid


class HeartbeatStatus(str, Enum):
    HEALTHY = "healthy"
    BUSY = "busy"
    IDLE = "idle"
    UNHEALTHY = "unhealthy"


class TraceStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class SpanStatus(str, Enum):
    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"


class AlertSeverity(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


class AlertType(str, Enum):
    LOOP = "loop"
    TIMEOUT = "timeout"
    TOOL_DEGRADED = "tool_degraded"
    COST_ANOMALY = "cost_anomaly"
    HEALTH_CHECK_FAIL = "health_check_fail"


class AlertStatus(str, Enum):
    OPEN = "open"
    ACKED = "acked"
    RESOLVED = "resolved"
    IGNORED = "ignored"


@dataclass
class AgentHeartbeat:
    agent_id: str
    timestamp: str
    status: HeartbeatStatus
    current_task_id: Optional[str]
    queue_depth: int
    memory_mb: Optional[float]
    cpu_percent: Optional[float]
    version: str


@dataclass
class AgentTrace:
    trace_id: str
    content_id: str
    pipeline_type: str
    start_time: str
    end_time: Optional[str]
    status: TraceStatus
    total_tokens: int
    total_cost_usd: float


@dataclass
class AgentSpan:
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    agent_id: str
    agent_role: str
    start_time: str
    end_time: Optional[str]
    duration_ms: int
    status: SpanStatus
    input_summary: str
    output_summary: str
    token_count: int
    model_version: str
    tool_calls: List[Dict[str, Any]]


@dataclass
class AgentAlert:
    id: str
    severity: AlertSeverity
    alert_type: AlertType
    agent_id: str
    trace_id: Optional[str]
    content_id: Optional[str]
    message: str
    created_at: str
    status: AlertStatus = AlertStatus.OPEN
    acked_by: Optional[str] = None
    resolved_at: Optional[str] = None
    root_cause: Optional[str] = None


# ─── Stores ───
_heartbeat_db: Dict[str, List[AgentHeartbeat]] = {}  # agent_id → heartbeats
_trace_db: Dict[str, AgentTrace] = {}                  # trace_id → trace
_span_db: Dict[str, List[AgentSpan]] = {}              # trace_id → spans
_alert_db: List[AgentAlert] = []


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _minutes_ago(minutes: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()


# ─── Heartbeat ───

def record_heartbeat(
    agent_id: str,
    status: str,
    current_task_id: Optional[str] = None,
    queue_depth: int = 0,
    memory_mb: Optional[float] = None,
    cpu_percent: Optional[float] = None,
    version: str = "",
) -> AgentHeartbeat:
    hb = AgentHeartbeat(
        agent_id=agent_id,
        timestamp=_now(),
        status=HeartbeatStatus(status),
        current_task_id=current_task_id,
        queue_depth=queue_depth,
        memory_mb=memory_mb,
        cpu_percent=cpu_percent,
        version=version,
    )
    _heartbeat_db.setdefault(agent_id, []).append(hb)
    return hb


def get_latest_heartbeat(agent_id: str) -> Optional[AgentHeartbeat]:
    hbs = _heartbeat_db.get(agent_id, [])
    return hbs[-1] if hbs else None


def is_agent_healthy(agent_id: str, max_missing_minutes: int = 2) -> bool:
    """Check if agent heartbeat is within acceptable window (default 2 min = ~3 cycles at 30s)."""
    hb = get_latest_heartbeat(agent_id)
    if not hb:
        return False
    try:
        last = datetime.fromisoformat(hb.timestamp)
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=max_missing_minutes)
        return last >= cutoff and hb.status != HeartbeatStatus.UNHEALTHY
    except Exception:
        return False


def get_agent_status(agent_id: str) -> Dict[str, Any]:
    hb = get_latest_heartbeat(agent_id)
    if not hb:
        return {"agent_id": agent_id, "status": "unknown", "healthy": False}
    return {
        "agent_id": agent_id,
        "status": hb.status.value,
        "current_task_id": hb.current_task_id,
        "queue_depth": hb.queue_depth,
        "version": hb.version,
        "healthy": is_agent_healthy(agent_id),
        "last_heartbeat": hb.timestamp,
    }


def get_dashboard() -> Dict[str, Any]:
    """Aggregate all agent statuses."""
    counts = {"healthy": 0, "busy": 0, "idle": 0, "unhealthy": 0, "unknown": 0}
    agents = []
    for agent_id in _heartbeat_db:
        st = get_agent_status(agent_id)
        counts[st["status"]] = counts.get(st["status"], 0) + 1
        agents.append(st)
    # Also count agents with no heartbeats as unknown
    return {
        "total_agents": len(agents),
        "status_counts": counts,
        "agents": agents,
    }


# ─── Trace / Span ───

def start_trace(trace_id: str, content_id: str, pipeline_type: str) -> AgentTrace:
    trace = AgentTrace(
        trace_id=trace_id,
        content_id=content_id,
        pipeline_type=pipeline_type,
        start_time=_now(),
        end_time=None,
        status=TraceStatus.RUNNING,
        total_tokens=0,
        total_cost_usd=0.0,
    )
    _trace_db[trace_id] = trace
    _span_db[trace_id] = []
    return trace


def finish_trace(trace_id: str, status: str) -> Optional[AgentTrace]:
    trace = _trace_db.get(trace_id)
    if trace:
        trace.status = TraceStatus(status)
        trace.end_time = _now()
        # Aggregate tokens from spans
        spans = _span_db.get(trace_id, [])
        trace.total_tokens = sum(s.token_count for s in spans)
    return trace


def record_span(
    trace_id: str,
    span_id: str,
    parent_span_id: Optional[str],
    agent_id: str,
    agent_role: str,
    start_time: str,
    end_time: Optional[str],
    status: str,
    input_summary: str,
    output_summary: str,
    token_count: int,
    model_version: str,
    tool_calls: Optional[List[Dict]] = None,
) -> AgentSpan:
    span = AgentSpan(
        span_id=span_id,
        trace_id=trace_id,
        parent_span_id=parent_span_id,
        agent_id=agent_id,
        agent_role=agent_role,
        start_time=start_time,
        end_time=end_time,
        duration_ms=0,
        status=SpanStatus(status),
        input_summary=input_summary,
        output_summary=output_summary,
        token_count=token_count,
        model_version=model_version,
        tool_calls=tool_calls or [],
    )
    if end_time and start_time:
        try:
            start = datetime.fromisoformat(start_time)
            end = datetime.fromisoformat(end_time)
            span.duration_ms = int((end - start).total_seconds() * 1000)
        except Exception:
            pass
    _span_db.setdefault(trace_id, []).append(span)
    return span


def get_trace(trace_id: str) -> Optional[Dict[str, Any]]:
    trace = _trace_db.get(trace_id)
    if not trace:
        return None
    spans = _span_db.get(trace_id, [])
    return {
        "trace_id": trace.trace_id,
        "content_id": trace.content_id,
        "pipeline_type": trace.pipeline_type,
        "start_time": trace.start_time,
        "end_time": trace.end_time,
        "status": trace.status.value,
        "total_tokens": trace.total_tokens,
        "total_cost_usd": trace.total_cost_usd,
        "spans": [
            {
                "span_id": s.span_id,
                "agent_id": s.agent_id,
                "agent_role": s.agent_role,
                "duration_ms": s.duration_ms,
                "status": s.status.value,
                "token_count": s.token_count,
                "model_version": s.model_version,
            }
            for s in spans
        ],
    }


def list_traces(
    content_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    traces = list(_trace_db.values())
    if content_id:
        traces = [t for t in traces if t.content_id == content_id]
    if status:
        traces = [t for t in traces if t.status.value == status]
    traces.sort(key=lambda t: t.start_time, reverse=True)
    return [get_trace(t.trace_id) for t in traces[:limit]]


# ─── Anomaly Detection ───

def detect_loop(agent_id: str, content_id: str, window_minutes: int = 5, threshold: int = 3) -> Optional[AgentAlert]:
    """Detect if same agent called for same content_id ≥threshold times in window."""
    spans = []
    for span_list in _span_db.values():
        for s in span_list:
            if s.agent_id == agent_id and s.trace_id in _trace_db:
                trace = _trace_db[s.trace_id]
                if trace.content_id == content_id:
                    spans.append(s)

    cutoff = _minutes_ago(window_minutes)
    recent = [s for s in spans if s.start_time >= cutoff]
    if len(recent) >= threshold:
        return _create_alert(
            severity=AlertSeverity.P1,
            alert_type=AlertType.LOOP,
            agent_id=agent_id,
            content_id=content_id,
            message=f"Agent {agent_id} loop detected: {len(recent)} calls to content {content_id} in {window_minutes}min",
        )
    return None


def detect_timeout(agent_id: str, span_id: str, max_duration_ms: int) -> Optional[AgentAlert]:
    """Detect if a single span exceeds duration threshold."""
    for span_list in _span_db.values():
        for s in span_list:
            if s.agent_id == agent_id and s.span_id == span_id:
                if s.duration_ms > max_duration_ms:
                    return _create_alert(
                        severity=AlertSeverity.P1,
                        alert_type=AlertType.TIMEOUT,
                        agent_id=agent_id,
                        trace_id=s.trace_id,
                        message=f"Agent {agent_id} span timeout: {s.duration_ms}ms > {max_duration_ms}ms",
                    )
    return None


def detect_tool_degraded(tool_name: str, fail_count_threshold: int = 3) -> Optional[AgentAlert]:
    """Detect if external tool failed consecutively."""
    all_tool_calls: List[Dict] = []
    for span_list in _span_db.values():
        for s in span_list:
            for tc in s.tool_calls:
                if tc.get("tool_name") == tool_name:
                    all_tool_calls.append(tc)

    # Check last N calls
    recent = all_tool_calls[-fail_count_threshold:]
    if len(recent) >= fail_count_threshold and all(tc.get("success") is False for tc in recent):
        return _create_alert(
            severity=AlertSeverity.P0,
            alert_type=AlertType.TOOL_DEGRADED,
            agent_id="system",
            message=f"Tool {tool_name} failed {fail_count_threshold} consecutive times",
        )
    return None


# ─── Alerts ───

def _create_alert(
    severity: AlertSeverity,
    alert_type: AlertType,
    agent_id: str,
    trace_id: Optional[str] = None,
    content_id: Optional[str] = None,
    message: str = "",
) -> AgentAlert:
    alert = AgentAlert(
        id=f"alt_{uuid.uuid4().hex[:12]}",
        severity=severity,
        alert_type=alert_type,
        agent_id=agent_id,
        trace_id=trace_id,
        content_id=content_id,
        message=message,
        created_at=_now(),
    )
    _alert_db.append(alert)
    return alert


def list_alerts(
    severity: Optional[str] = None,
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> List[AgentAlert]:
    alerts = _alert_db[:]
    if severity:
        alerts = [a for a in alerts if a.severity.value == severity]
    if agent_id:
        alerts = [a for a in alerts if a.agent_id == agent_id]
    if status:
        alerts = [a for a in alerts if a.status.value == status]
    alerts.sort(key=lambda a: a.created_at, reverse=True)
    return alerts[-limit:]


def ack_alert(alert_id: str, acked_by: str) -> Optional[AgentAlert]:
    for a in _alert_db:
        if a.id == alert_id:
            a.status = AlertStatus.ACKED
            a.acked_by = acked_by
            return a
    return None


def resolve_alert(alert_id: str, root_cause: Optional[str] = None) -> Optional[AgentAlert]:
    for a in _alert_db:
        if a.id == alert_id:
            a.status = AlertStatus.RESOLVED
            a.resolved_at = _now()
            a.root_cause = root_cause
            return a
    return None
