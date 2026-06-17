"""AgentCockpit — W17: unified console aggregating Hub + Watch + Metrics.

Aligned with detailed design §5.14 / PRD V2.4 §7.5.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.services import agent_hub as hub
from src.services import agent_watch as watch
from src.services import agent_metrics as metrics


# ─── Cockpit Views ───

def get_agent_overview(agent_id: str) -> Optional[Dict[str, Any]]:
    """Unified single-agent view: registration + status + latest metrics + alerts."""
    agent = hub.get_agent(agent_id)
    if not agent:
        return None

    status = watch.get_agent_status(agent_id)
    metric = metrics.get_agent_metrics(agent_id)
    active_config = hub.get_active_config(agent_id)
    deps = hub.check_all_dependencies(agent_id)
    alerts = watch.list_alerts(agent_id=agent_id, status="open", limit=5)

    return {
        "agent_id": agent.id,
        "name": agent.name,
        "role": agent.role,
        "status": agent.status.value,
        "environment": getattr(agent, "environment", ""),
        "version": getattr(agent, "version", ""),
        "heartbeat": status,
        "active_config": {
            "version": active_config.version,
            "sha256": active_config.sha256,
            "activated_at": active_config.activated_at,
        } if active_config else None,
        "dependencies": {
            "total": deps.get("total", 0),
            "healthy": deps.get("healthy", 0),
            "degraded": deps.get("degraded", 0),
            "down": deps.get("down", 0),
            "overall": deps.get("overall", "unknown"),
        },
        "latest_metrics": metric,
        "open_alerts": [
            {
                "id": a.id,
                "severity": a.severity.value,
                "alert_type": a.alert_type.value,
                "message": a.message,
                "created_at": a.created_at,
            }
            for a in alerts
        ],
    }


def get_cockpit_dashboard() -> Dict[str, Any]:
    """Full cockpit dashboard: all agents, open alerts, overall metrics, active traces."""
    agents = hub.list_agents()
    watch_dash = watch.get_dashboard()
    overall = metrics.get_overall_metrics(window_minutes=60)
    open_alerts = watch.list_alerts(status="open", limit=20)
    traces = watch.list_traces(status="running", limit=10)

    agent_cards = []
    for a in agents:
        status = watch.get_agent_status(a.id)
        metric = metrics.get_agent_metrics(a.id)
        agent_cards.append({
            "agent_id": a.id,
            "name": a.name,
            "role": a.role,
            "status": a.status.value,
            "healthy": status.get("healthy", False) if status else False,
            "queue_depth": status.get("queue_depth", 0) if status else 0,
            "version": getattr(a, "version", ""),
            "completion_rate": metric.get("completion_rate", 0.0) if metric else 0.0,
            "total_tasks_1h": metric.get("total_tasks", 0) if metric else 0,
        })

    return {
        "agents": agent_cards,
        "agent_summary": {
            "total": len(agents),
            "healthy": sum(1 for c in agent_cards if c["healthy"]),
            "unhealthy": sum(1 for c in agent_cards if not c["healthy"]),
        },
        "watch_dashboard": watch_dash,
        "overall_metrics": overall,
        "open_alerts": [
            {
                "id": a.id,
                "severity": a.severity.value,
                "alert_type": a.alert_type.value,
                "agent_id": a.agent_id,
                "message": a.message,
                "created_at": a.created_at,
            }
            for a in open_alerts
        ],
        "active_traces": traces,
    }


def get_alert_summary() -> Dict[str, Any]:
    """Alert summary by severity and type."""
    all_alerts = watch.list_alerts(limit=1000)
    by_severity: Dict[str, int] = {"P0": 0, "P1": 0, "P2": 0}
    by_type: Dict[str, int] = {}
    by_status: Dict[str, int] = {"open": 0, "acked": 0, "resolved": 0}

    for a in all_alerts:
        by_severity[a.severity.value] = by_severity.get(a.severity.value, 0) + 1
        by_type[a.alert_type.value] = by_type.get(a.alert_type.value, 0) + 1
        by_status[a.status.value] = by_status.get(a.status.value, 0) + 1

    return {
        "total": len(all_alerts),
        "by_severity": by_severity,
        "by_type": by_type,
        "by_status": by_status,
        "latest": [
            {"id": a.id, "severity": a.severity.value, "message": a.message, "created_at": a.created_at}
            for a in sorted(all_alerts, key=lambda x: x.created_at, reverse=True)[:5]
        ],
    }


def run_health_check(agent_id: str) -> Dict[str, Any]:
    """Trigger a manual dependency health check for an agent."""
    agent = hub.get_agent(agent_id)
    if not agent:
        return {"agent_id": agent_id, "found": False, "results": []}

    deps = hub.check_all_dependencies(agent_id)
    all_healthy = deps.get("overall") == "healthy"

    return {
        "agent_id": agent_id,
        "found": True,
        "all_healthy": all_healthy,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "results": deps,
    }


def get_recent_activity(limit: int = 20) -> List[Dict[str, Any]]:
    """Recent activity stream: tasks + alerts + heartbeats merged."""
    # Gather recent tasks
    tasks = metrics.list_tasks(limit=limit)
    # Gather recent alerts
    alerts = watch.list_alerts(limit=limit)
    # Gather recent heartbeats (latest per agent)
    heartbeats = []
    for agent_id, hbs in watch._heartbeat_db.items():
        if hbs:
            hb = hbs[-1]
            heartbeats.append({
                "type": "heartbeat",
                "timestamp": hb.timestamp,
                "agent_id": hb.agent_id,
                "status": hb.status.value,
                "queue_depth": hb.queue_depth,
            })

    # Merge and sort by timestamp descending
    stream = []
    for t in tasks:
        stream.append({
            "type": "task",
            "timestamp": t["start_time"],
            "agent_id": t["agent_id"],
            "agent_role": t["agent_role"],
            "outcome": t["outcome"],
            "content_id": t["content_id"],
        })
    for a in alerts:
        stream.append({
            "type": "alert",
            "timestamp": a.created_at,
            "agent_id": a.agent_id,
            "severity": a.severity.value,
            "alert_type": a.alert_type.value,
            "message": a.message,
        })
    stream.extend(heartbeats)

    stream.sort(key=lambda x: x["timestamp"], reverse=True)
    return stream[:limit]
