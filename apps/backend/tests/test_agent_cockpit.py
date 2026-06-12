"""Tests for AgentCockpit (W17).

Red-Green TDD for:
  - Single agent overview (Hub + Watch + Metrics aggregation)
  - Full dashboard
  - Alert summary
  - Recent activity stream
  - Manual health check
"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.services import agent_hub as hub
from src.services import agent_watch as watch
from src.services import agent_metrics as metrics
from src.services import agent_cockpit as cockpit


@pytest.fixture(autouse=True)
def clear_all():
    hub._agent_db.clear()
    hub._config_db.clear()
    hub._dep_db.clear()
    hub._perm_db.clear()
    watch._heartbeat_db.clear()
    watch._trace_db.clear()
    watch._span_db.clear()
    watch._alert_db.clear()
    metrics._task_db.clear()
    metrics._metric_cache.clear()
    yield


def _seed_agent(name: str, role: str):
    return hub.register_agent(name, role)


def _seed_heartbeat(agent_id: str, status: str = "healthy"):
    watch.record_heartbeat(agent_id, status, queue_depth=2, version="v1.0")


def _seed_task(agent_id: str, role: str, outcome: str = "success"):
    now = metrics._now()
    return metrics.record_task(
        agent_id=agent_id, agent_role=role, content_id="c-1",
        outcome=outcome, start_time=now, duration_ms=1000,
        token_count=100, cost_usd=0.002,
    )


def _seed_alert(agent_id: str, severity: str = "P1", alert_type: str = "timeout"):
    from src.services.agent_watch import AlertSeverity, AlertType
    watch._create_alert(AlertSeverity(severity), AlertType(alert_type), agent_id, message="test alert")


# ─── Agent Overview ───

def test_agent_overview():
    agent = _seed_agent("ContentForge", "CONTENT_FORGE")
    _seed_heartbeat(agent.id)
    _seed_task(agent.id, "CONTENT_FORGE")

    overview = cockpit.get_agent_overview(agent.id)
    assert overview is not None
    assert overview["agent_id"] == agent.id
    assert overview["name"] == "ContentForge"
    assert overview["heartbeat"]["healthy"] is True
    assert overview["latest_metrics"]["total_tasks"] == 1


def test_agent_overview_not_found():
    assert cockpit.get_agent_overview("nonexistent") is None


def test_agent_overview_with_alerts():
    agent = _seed_agent("ContentForge", "CONTENT_FORGE")
    _seed_heartbeat(agent.id)
    _seed_alert(agent.id, "P0", "loop")

    overview = cockpit.get_agent_overview(agent.id)
    assert len(overview["open_alerts"]) == 1
    assert overview["open_alerts"][0]["severity"] == "P0"


# ─── Dashboard ───

def test_cockpit_dashboard():
    a1 = _seed_agent("ContentForge", "CONTENT_FORGE")
    a2 = _seed_agent("ComplianceGuard", "COMPLIANCE")
    _seed_heartbeat(a1.id, "healthy")
    _seed_heartbeat(a2.id, "unhealthy")
    _seed_task(a1.id, "CONTENT_FORGE")
    _seed_alert(a2.id, "P1", "timeout")

    dash = cockpit.get_cockpit_dashboard()
    assert len(dash["agents"]) == 2
    assert dash["agent_summary"]["total"] == 2
    assert dash["agent_summary"]["healthy"] == 1
    assert dash["agent_summary"]["unhealthy"] == 1
    assert len(dash["open_alerts"]) == 1
    assert dash["overall_metrics"]["total_tasks"] == 1


def test_dashboard_empty():
    dash = cockpit.get_cockpit_dashboard()
    assert dash["agent_summary"]["total"] == 0
    assert dash["open_alerts"] == []


# ─── Alert Summary ───

def test_alert_summary():
    _seed_alert("agt-1", "P0", "loop")
    _seed_alert("agt-1", "P1", "timeout")
    _seed_alert("agt-2", "P1", "timeout")

    summary = cockpit.get_alert_summary()
    assert summary["total"] == 3
    assert summary["by_severity"]["P0"] == 1
    assert summary["by_severity"]["P1"] == 2
    assert summary["by_type"]["timeout"] == 2
    assert summary["by_type"]["loop"] == 1
    assert summary["by_status"]["open"] == 3
    assert len(summary["latest"]) == 3


def test_alert_summary_empty():
    summary = cockpit.get_alert_summary()
    assert summary["total"] == 0
    assert summary["by_severity"] == {"P0": 0, "P1": 0, "P2": 0}


# ─── Activity Stream ───

def test_recent_activity():
    agent = _seed_agent("ContentForge", "CONTENT_FORGE")
    _seed_heartbeat(agent.id)
    _seed_task(agent.id, "CONTENT_FORGE")
    _seed_alert(agent.id, "P1", "timeout")

    activity = cockpit.get_recent_activity(limit=10)
    assert len(activity) == 3
    types = {a["type"] for a in activity}
    assert types == {"task", "alert", "heartbeat"}
    # Should be sorted by timestamp desc
    assert activity[0]["timestamp"] >= activity[-1]["timestamp"]


def test_recent_activity_respects_limit():
    agent = _seed_agent("ContentForge", "CONTENT_FORGE")
    for _ in range(5):
        _seed_task(agent.id, "CONTENT_FORGE")
    activity = cockpit.get_recent_activity(limit=3)
    assert len(activity) == 3


# ─── Health Check ───

def test_run_health_check():
    agent = _seed_agent("ContentForge", "CONTENT_FORGE")
    from src.services.agent_hub import DepType
    hub.declare_dependency(agent.id, DepType.TOOL, "Redis")
    result = cockpit.run_health_check(agent.id)
    assert result["found"] is True
    assert result["all_healthy"] is True
    assert result["results"]["total"] == 1


def test_run_health_check_not_found():
    result = cockpit.run_health_check("nonexistent")
    assert result["found"] is False
