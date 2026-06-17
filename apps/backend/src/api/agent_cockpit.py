"""AgentCockpit API — W17: unified console.

Routes:
  GET  /agent-cockpit/dashboard          # Full dashboard
  GET  /agent-cockpit/agents/{id}        # Single agent overview
  GET  /agent-cockpit/alerts/summary     # Alert summary
  GET  /agent-cockpit/activity           # Recent activity stream
  POST /agent-cockpit/agents/{id}/health-check  # Manual health check
"""

from fastapi import APIRouter, HTTPException

from src.services import agent_cockpit as cockpit

router = APIRouter(prefix="/agent-cockpit", tags=["agent-cockpit"])


@router.get("/dashboard")
def dashboard():
    return cockpit.get_cockpit_dashboard()


@router.get("/agents/{agent_id}")
def agent_overview(agent_id: str):
    overview = cockpit.get_agent_overview(agent_id)
    if not overview:
        raise HTTPException(status_code=404, detail="Agent not found")
    return overview


@router.get("/alerts/summary")
def alert_summary():
    return cockpit.get_alert_summary()


@router.get("/activity")
def recent_activity(limit: int = 20):
    return cockpit.get_recent_activity(limit=limit)


@router.post("/agents/{agent_id}/health-check")
def health_check(agent_id: str):
    result = cockpit.run_health_check(agent_id)
    if not result["found"]:
        raise HTTPException(status_code=404, detail="Agent not found")
    return result
