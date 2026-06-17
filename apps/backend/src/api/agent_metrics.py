"""AgentMetrics API — W16.

Routes:
  POST /agent-metrics/tasks              # Record a task
  GET  /agent-metrics/tasks              # List tasks
  GET  /agent-metrics/agents/{id}        # Agent metrics
  GET  /agent-metrics/overall            # Overall metrics
  POST /agent-metrics/tasks/{id}/score   # Submit quality score
  GET  /agent-metrics/cost/by-agent      # Cost breakdown by agent
  GET  /agent-metrics/cost/by-content    # Cost breakdown by content
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.services import agent_metrics as am

router = APIRouter(prefix="/agent-metrics", tags=["agent-metrics"])


# ─── Schemas ───

class RecordTaskRequest(BaseModel):
    agent_id: str
    agent_role: str
    content_id: str
    outcome: str = "success"
    start_time: str
    end_time: Optional[str] = None
    duration_ms: int = 0
    token_count: int = 0
    cost_usd: float = 0.0
    model_version: str = ""
    pipeline_type: str = ""
    quality_score: Optional[float] = None


class SubmitScoreRequest(BaseModel):
    score: float = Field(..., ge=0.0, le=100.0)


# ─── Tasks ───

@router.post("/tasks")
def record_task(req: RecordTaskRequest):
    task = am.record_task(
        agent_id=req.agent_id,
        agent_role=req.agent_role,
        content_id=req.content_id,
        outcome=req.outcome,
        start_time=req.start_time,
        end_time=req.end_time,
        duration_ms=req.duration_ms,
        token_count=req.token_count,
        cost_usd=req.cost_usd,
        model_version=req.model_version,
        pipeline_type=req.pipeline_type,
        quality_score=req.quality_score,
    )
    return {"task_id": task.task_id, "status": "recorded"}


@router.get("/tasks")
def list_tasks(
    agent_id: Optional[str] = None,
    content_id: Optional[str] = None,
    outcome: Optional[str] = None,
    limit: int = 100,
):
    return am.list_tasks(agent_id=agent_id, content_id=content_id, outcome=outcome, limit=limit)


# ─── Metrics ───

@router.get("/agents/{agent_id}")
def agent_metrics(agent_id: str, window_minutes: int = 60):
    metrics = am.get_agent_metrics(agent_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="No metrics found for agent")
    return metrics


@router.get("/overall")
def overall_metrics(window_minutes: int = 60):
    return am.get_overall_metrics(window_minutes=window_minutes)


# ─── Quality Score ───

@router.post("/tasks/{task_id}/score")
def submit_score(task_id: str, req: SubmitScoreRequest):
    task = am.submit_quality_score(task_id, req.score)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task.task_id, "quality_score": task.quality_score}


# ─── Cost Attribution ───

@router.get("/cost/by-agent")
def cost_by_agent(window_minutes: int = 60):
    return am.get_cost_by_agent(window_minutes=window_minutes)


@router.get("/cost/by-content")
def cost_by_content(content_id: str):
    return am.get_cost_by_content(content_id=content_id)
