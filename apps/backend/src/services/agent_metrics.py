"""AgentMetrics — W16: task completion, token cost, latency distribution, quality scoring.

Aligned with detailed design §5.13 / PRD V2.4 §7.4.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
import statistics


class TaskOutcome(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class TaskRecord:
    task_id: str
    agent_id: str
    agent_role: str
    content_id: str
    outcome: TaskOutcome
    start_time: str
    end_time: Optional[str]
    duration_ms: int
    token_count: int
    cost_usd: float
    model_version: str
    pipeline_type: str
    quality_score: Optional[float] = None  # 0–100


@dataclass
class AgentMetric:
    agent_id: str
    agent_role: str
    window_start: str
    window_end: str
    total_tasks: int
    success_count: int
    failure_count: int
    timeout_count: int
    cancelled_count: int
    avg_duration_ms: float
    p50_duration_ms: float
    p95_duration_ms: float
    p99_duration_ms: float
    total_tokens: int
    total_cost_usd: float
    avg_quality_score: Optional[float]


# ─── Stores ───
_task_db: List[TaskRecord] = []
_metric_cache: Dict[str, AgentMetric] = {}  # agent_id → latest metric


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _minutes_ago(minutes: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()


def _parse_dt(iso: str) -> datetime:
    return datetime.fromisoformat(iso)


# ─── Task Recording ───

def record_task(
    agent_id: str,
    agent_role: str,
    content_id: str,
    outcome: str,
    start_time: str,
    end_time: Optional[str] = None,
    duration_ms: int = 0,
    token_count: int = 0,
    cost_usd: float = 0.0,
    model_version: str = "",
    pipeline_type: str = "",
    quality_score: Optional[float] = None,
) -> TaskRecord:
    task = TaskRecord(
        task_id=f"tsk_{uuid.uuid4().hex[:12]}",
        agent_id=agent_id,
        agent_role=agent_role,
        content_id=content_id,
        outcome=TaskOutcome(outcome),
        start_time=start_time,
        end_time=end_time or _now(),
        duration_ms=duration_ms,
        token_count=token_count,
        cost_usd=cost_usd,
        model_version=model_version,
        pipeline_type=pipeline_type,
        quality_score=quality_score,
    )
    _task_db.append(task)
    return task


def list_tasks(
    agent_id: Optional[str] = None,
    content_id: Optional[str] = None,
    outcome: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    tasks = _task_db[:]
    if agent_id:
        tasks = [t for t in tasks if t.agent_id == agent_id]
    if content_id:
        tasks = [t for t in tasks if t.content_id == content_id]
    if outcome:
        tasks = [t for t in tasks if t.outcome.value == outcome]
    tasks.sort(key=lambda t: t.start_time, reverse=True)
    return [
        {
            "task_id": t.task_id,
            "agent_id": t.agent_id,
            "agent_role": t.agent_role,
            "content_id": t.content_id,
            "outcome": t.outcome.value,
            "duration_ms": t.duration_ms,
            "token_count": t.token_count,
            "cost_usd": t.cost_usd,
            "model_version": t.model_version,
            "pipeline_type": t.pipeline_type,
            "quality_score": t.quality_score,
            "start_time": t.start_time,
        }
        for t in tasks[:limit]
    ]


# ─── Metrics Aggregation ───

def compute_agent_metrics(
    agent_id: str,
    window_minutes: int = 60,
) -> Optional[AgentMetric]:
    """Compute aggregate metrics for an agent over a time window."""
    cutoff = _minutes_ago(window_minutes)
    tasks = [t for t in _task_db if t.agent_id == agent_id and t.start_time >= cutoff]
    if not tasks:
        return None

    durations = [t.duration_ms for t in tasks]
    tokens = [t.token_count for t in tasks]
    costs = [t.cost_usd for t in tasks]
    qualities = [t.quality_score for t in tasks if t.quality_score is not None]

    def _percentile(data: List[float], p: float) -> float:
        if not data:
            return 0.0
        s = sorted(data)
        k = (len(s) - 1) * p / 100.0
        f = int(k)
        c = f + 1 if f + 1 < len(s) else f
        if f == c:
            return s[f]
        return s[f] * (c - k) + s[c] * (k - f)

    metric = AgentMetric(
        agent_id=agent_id,
        agent_role=tasks[0].agent_role,
        window_start=cutoff,
        window_end=_now(),
        total_tasks=len(tasks),
        success_count=sum(1 for t in tasks if t.outcome == TaskOutcome.SUCCESS),
        failure_count=sum(1 for t in tasks if t.outcome == TaskOutcome.FAILURE),
        timeout_count=sum(1 for t in tasks if t.outcome == TaskOutcome.TIMEOUT),
        cancelled_count=sum(1 for t in tasks if t.outcome == TaskOutcome.CANCELLED),
        avg_duration_ms=statistics.mean(durations) if durations else 0.0,
        p50_duration_ms=_percentile(durations, 50),
        p95_duration_ms=_percentile(durations, 95),
        p99_duration_ms=_percentile(durations, 99),
        total_tokens=sum(tokens),
        total_cost_usd=sum(costs),
        avg_quality_score=statistics.mean(qualities) if qualities else None,
    )
    _metric_cache[agent_id] = metric
    return metric


def get_agent_metrics(agent_id: str) -> Optional[Dict[str, Any]]:
    """Return latest cached metrics for an agent, computing if absent."""
    metric = _metric_cache.get(agent_id)
    if not metric:
        metric = compute_agent_metrics(agent_id)
    if not metric:
        return None
    return {
        "agent_id": metric.agent_id,
        "agent_role": metric.agent_role,
        "window_start": metric.window_start,
        "window_end": metric.window_end,
        "total_tasks": metric.total_tasks,
        "success_count": metric.success_count,
        "failure_count": metric.failure_count,
        "timeout_count": metric.timeout_count,
        "cancelled_count": metric.cancelled_count,
        "completion_rate": metric.success_count / metric.total_tasks if metric.total_tasks else 0.0,
        "avg_duration_ms": metric.avg_duration_ms,
        "p50_duration_ms": metric.p50_duration_ms,
        "p95_duration_ms": metric.p95_duration_ms,
        "p99_duration_ms": metric.p99_duration_ms,
        "total_tokens": metric.total_tokens,
        "total_cost_usd": metric.total_cost_usd,
        "avg_quality_score": metric.avg_quality_score,
    }


def get_overall_metrics(window_minutes: int = 60) -> Dict[str, Any]:
    """Aggregate metrics across all agents."""
    cutoff = _minutes_ago(window_minutes)
    tasks = [t for t in _task_db if t.start_time >= cutoff]
    if not tasks:
        return {
            "window_start": cutoff,
            "window_end": _now(),
            "total_tasks": 0,
            "total_agents": 0,
            "overall_completion_rate": 0.0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
        }

    agents = {t.agent_id for t in tasks}
    success = sum(1 for t in tasks if t.outcome == TaskOutcome.SUCCESS)
    return {
        "window_start": cutoff,
        "window_end": _now(),
        "total_tasks": len(tasks),
        "total_agents": len(agents),
        "overall_completion_rate": success / len(tasks),
        "total_tokens": sum(t.token_count for t in tasks),
        "total_cost_usd": sum(t.cost_usd for t in tasks),
    }


# ─── Quality Scoring ───

def submit_quality_score(task_id: str, score: float) -> Optional[TaskRecord]:
    """Submit a quality score (0–100) for a completed task."""
    for t in _task_db:
        if t.task_id == task_id:
            t.quality_score = max(0.0, min(100.0, score))
            return t
    return None


# ─── Token Cost Attribution ───

def get_cost_by_agent(window_minutes: int = 60) -> List[Dict[str, Any]]:
    """Break down token cost by agent."""
    cutoff = _minutes_ago(window_minutes)
    tasks = [t for t in _task_db if t.start_time >= cutoff]
    result: Dict[str, Dict[str, Any]] = {}
    for t in tasks:
        if t.agent_id not in result:
            result[t.agent_id] = {
                "agent_id": t.agent_id,
                "agent_role": t.agent_role,
                "task_count": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
            }
        result[t.agent_id]["task_count"] += 1
        result[t.agent_id]["total_tokens"] += t.token_count
        result[t.agent_id]["total_cost_usd"] += t.cost_usd
    return sorted(result.values(), key=lambda x: x["total_cost_usd"], reverse=True)


def get_cost_by_content(content_id: str) -> List[Dict[str, Any]]:
    """Break down token cost by agent for a specific content."""
    tasks = [t for t in _task_db if t.content_id == content_id]
    result: Dict[str, Dict[str, Any]] = {}
    for t in tasks:
        if t.agent_id not in result:
            result[t.agent_id] = {
                "agent_id": t.agent_id,
                "agent_role": t.agent_role,
                "task_count": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
            }
        result[t.agent_id]["task_count"] += 1
        result[t.agent_id]["total_tokens"] += t.token_count
        result[t.agent_id]["total_cost_usd"] += t.cost_usd
    return list(result.values())
