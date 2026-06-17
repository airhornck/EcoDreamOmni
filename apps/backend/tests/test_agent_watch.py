"""Tests for AgentWatch (W15–W16).

Red-Green TDD for:
  - Heartbeat recording & health check
  - Dashboard aggregation
  - Trace/Span lifecycle
  - Anomaly detection (loop, timeout, tool degraded)
  - Alert lifecycle
"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.services import agent_watch as aw
from src.services.agent_watch import HeartbeatStatus, TraceStatus, AlertSeverity, AlertType, AlertStatus


@pytest.fixture(autouse=True)
def clear_db():
    aw._heartbeat_db.clear()
    aw._trace_db.clear()
    aw._span_db.clear()
    aw._alert_db.clear()
    yield


# ─── Heartbeat ───

def test_record_heartbeat():
    hb = aw.record_heartbeat("agt-1", "healthy", queue_depth=2, version="v1.2")
    assert hb.agent_id == "agt-1"
    assert hb.status == HeartbeatStatus.HEALTHY
    assert hb.queue_depth == 2


def test_is_agent_healthy():
    aw.record_heartbeat("agt-1", "healthy")
    assert aw.is_agent_healthy("agt-1") is True


def test_is_agent_unhealthy():
    aw.record_heartbeat("agt-1", "unhealthy")
    assert aw.is_agent_healthy("agt-1") is False


def test_is_agent_healthy_missing():
    assert aw.is_agent_healthy("nonexistent") is False


def test_get_agent_status():
    aw.record_heartbeat("agt-1", "busy", current_task_id="task-1", queue_depth=3, version="v1")
    st = aw.get_agent_status("agt-1")
    assert st["status"] == "busy"
    assert st["queue_depth"] == 3
    assert st["healthy"] is True


def test_dashboard():
    aw.record_heartbeat("agt-1", "healthy")
    aw.record_heartbeat("agt-2", "busy")
    aw.record_heartbeat("agt-3", "unhealthy")
    dash = aw.get_dashboard()
    assert dash["status_counts"]["healthy"] == 1
    assert dash["status_counts"]["busy"] == 1
    assert dash["status_counts"]["unhealthy"] == 1
    assert len(dash["agents"]) == 3


# ─── Trace / Span ───

def test_trace_lifecycle():
    trace = aw.start_trace("trace-1", "content-1", "CONTENT_CREATION")
    assert trace.trace_id == "trace-1"
    assert trace.status == TraceStatus.RUNNING

    now = aw._now()
    span = aw.record_span(
        trace_id="trace-1",
        span_id="span-1",
        parent_span_id=None,
        agent_id="agt-cf",
        agent_role="CONTENT_FORGE",
        start_time=now,
        end_time=now,
        status="ok",
        input_summary="topic: dog food",
        output_summary="draft generated",
        token_count=150,
        model_version="gpt-4o",
    )
    assert span.duration_ms == 0

    finished = aw.finish_trace("trace-1", "completed")
    assert finished.status == TraceStatus.COMPLETED
    assert finished.total_tokens == 150


def test_get_trace():
    aw.start_trace("trace-1", "content-1", "CONTENT_CREATION")
    now = aw._now()
    aw.record_span(
        trace_id="trace-1", span_id="span-1", parent_span_id=None,
        agent_id="agt-cf", agent_role="CONTENT_FORGE",
        start_time=now, end_time=now,
        status="ok", input_summary="in", output_summary="out", token_count=100, model_version="gpt-4o",
    )
    result = aw.get_trace("trace-1")
    assert result["trace_id"] == "trace-1"
    assert len(result["spans"]) == 1


def test_list_traces():
    aw.start_trace("trace-1", "content-1", "CONTENT_CREATION")
    aw.start_trace("trace-2", "content-2", "DATA_ANALYSIS")
    traces = aw.list_traces()
    assert len(traces) == 2


def test_list_traces_filter():
    aw.start_trace("trace-1", "content-1", "CONTENT_CREATION")
    aw.start_trace("trace-2", "content-2", "DATA_ANALYSIS")
    filtered = aw.list_traces(content_id="content-1")
    assert len(filtered) == 1
    assert filtered[0]["content_id"] == "content-1"


# ─── Anomaly Detection ───

def test_detect_loop():
    # Create 3 traces for same content + agent → loop detected
    now = aw._now()
    for tid in ["t-1", "t-2", "t-3"]:
        aw.start_trace(tid, "c-loop", "P")
        aw.record_span(
            trace_id=tid, span_id=f"s-{tid}", parent_span_id=None,
            agent_id="agt-loop", agent_role="TEST",
            start_time=now, end_time=now,
            status="ok", input_summary="in", output_summary="out", token_count=10, model_version="gpt-4o",
        )

    alert = aw.detect_loop("agt-loop", "c-loop", window_minutes=60, threshold=3)
    assert alert is not None
    assert alert.alert_type == AlertType.LOOP
    assert alert.severity == AlertSeverity.P1


def test_detect_loop_below_threshold():
    aw.start_trace("t-1", "c-safe", "P")
    now = aw._now()
    aw.record_span(
        trace_id="t-1", span_id="s-1", parent_span_id=None,
        agent_id="agt-safe", agent_role="TEST",
        start_time=now, end_time=now,
        status="ok", input_summary="in", output_summary="out", token_count=10, model_version="gpt-4o",
    )
    alert = aw.detect_loop("agt-safe", "c-safe", window_minutes=60, threshold=3)
    assert alert is None


def test_detect_timeout():
    aw.start_trace("t-1", "c-1", "P")
    aw.record_span(
        trace_id="t-1", span_id="s-slow", parent_span_id=None,
        agent_id="agt-slow", agent_role="TEST",
        start_time="2026-05-14T10:00:00+00:00", end_time="2026-05-14T10:01:30+00:00",
        status="ok", input_summary="in", output_summary="out", token_count=10, model_version="gpt-4o",
    )
    alert = aw.detect_timeout("agt-slow", "s-slow", max_duration_ms=30000)
    assert alert is not None
    assert alert.alert_type == AlertType.TIMEOUT


def test_detect_tool_degraded():
    now = aw._now()
    for i in range(3):
        aw.start_trace(f"t-{i}", "c-1", "P")
        aw.record_span(
            trace_id=f"t-{i}", span_id=f"s-{i}", parent_span_id=None,
            agent_id="agt-tool", agent_role="TEST",
            start_time=now, end_time=now,
            status="ok", input_summary="in", output_summary="out", token_count=10, model_version="gpt-4o",
            tool_calls=[{"tool_name": "xhs-api", "success": False}],
        )
    alert = aw.detect_tool_degraded("xhs-api", fail_count_threshold=3)
    assert alert is not None
    assert alert.alert_type == AlertType.TOOL_DEGRADED
    assert alert.severity == AlertSeverity.P0


# ─── Alerts ───

def test_alert_lifecycle():
    alert = aw._create_alert(AlertSeverity.P1, AlertType.TIMEOUT, "agt-1", message="Timeout")
    assert alert.status == AlertStatus.OPEN

    acked = aw.ack_alert(alert.id, "alice")
    assert acked.status == AlertStatus.ACKED
    assert acked.acked_by == "alice"

    resolved = aw.resolve_alert(alert.id, "Root: network latency")
    assert resolved.status == AlertStatus.RESOLVED
    assert resolved.root_cause == "Root: network latency"


def test_list_alerts_filter():
    aw._create_alert(AlertSeverity.P0, AlertType.LOOP, "agt-1", message="P0")
    aw._create_alert(AlertSeverity.P1, AlertType.TIMEOUT, "agt-2", message="P1")
    p0 = aw.list_alerts(severity="P0")
    assert len(p0) == 1
    assert p0[0].severity == AlertSeverity.P0


def test_list_alerts_by_agent():
    aw._create_alert(AlertSeverity.P1, AlertType.TIMEOUT, "agt-a", message="A")
    aw._create_alert(AlertSeverity.P1, AlertType.TIMEOUT, "agt-b", message="B")
    a_alerts = aw.list_alerts(agent_id="agt-a")
    assert len(a_alerts) == 1
    assert a_alerts[0].agent_id == "agt-a"
