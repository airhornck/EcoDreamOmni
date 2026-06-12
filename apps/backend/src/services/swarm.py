"""Swarm Mode — v4.0 Phase 9.

Fan-out/Fan-in 并行执行：同时调度多个相同 Agent 实例，聚合结果。
依赖 Agent Fleet (P8-3) 提供实例池。
MVP: 内存调度，无持久化。
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.services.agent_fleet import route_task


@dataclass
class SwarmTask:
    """单个 Swarm 子任务."""
    task_id: str
    agent_type: str
    input_payload: Dict[str, Any]
    assigned_instance_id: str = ""
    status: str = "pending"  # pending / running / completed / failed
    result: Optional[Dict[str, Any]] = None
    error: str = ""
    started_at: str = ""
    completed_at: str = ""


@dataclass
class SwarmJob:
    """Swarm 作业：一组并行子任务的集合."""
    job_id: str
    agent_type: str
    fleet_id: str
    tenant_id: str = ""
    tasks: List[SwarmTask] = field(default_factory=list)
    status: str = "pending"  # pending / running / aggregating / completed / failed
    aggregated_result: Optional[Dict[str, Any]] = None
    created_at: str = ""
    completed_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


# ─── In-memory registry ───
_swarm_jobs: Dict[str, SwarmJob] = {}


def _new_id(prefix: str = "swarm") -> str:
    import secrets
    return f"{prefix}_{secrets.token_urlsafe(8)}"


def create_swarm_job(
    agent_type: str,
    fleet_id: str,
    task_inputs: List[Dict[str, Any]],
    tenant_id: str = "",
) -> SwarmJob:
    """Create a Swarm job with multiple task inputs."""
    job = SwarmJob(
        job_id=_new_id("job"),
        agent_type=agent_type,
        fleet_id=fleet_id,
        tenant_id=tenant_id,
        tasks=[
            SwarmTask(
                task_id=_new_id("task"),
                agent_type=agent_type,
                input_payload=inp,
            )
            for inp in task_inputs
        ],
    )
    _swarm_jobs[job.job_id] = job
    return job


def get_swarm_job(job_id: str) -> Optional[SwarmJob]:
    return _swarm_jobs.get(job_id)


def list_swarm_jobs(tenant_id: str = "") -> List[SwarmJob]:
    if tenant_id:
        return [j for j in _swarm_jobs.values() if j.tenant_id == tenant_id]
    return list(_swarm_jobs.values())


async def execute_swarm_fan_out(
    job_id: str,
    task_handler: Any,  # Callable[[Dict], Awaitable[Dict]]
    max_concurrency: int = 5,
) -> SwarmJob:
    """
    Fan-out: execute all tasks in parallel with concurrency limit.
    task_handler: async function(task_input) -> result_dict
    """
    job = _swarm_jobs.get(job_id)
    if not job:
        raise ValueError(f"Swarm job {job_id} not found")

    job.status = "running"
    semaphore = asyncio.Semaphore(max_concurrency)

    async def _run_one(task: SwarmTask) -> None:
        async with semaphore:
            # Route to an available instance (optional — MVP fallback to direct execution)
            instance = route_task(job.fleet_id)
            if instance:
                task.assigned_instance_id = instance.instance_id

            task.status = "running"
            task.started_at = datetime.now(timezone.utc).isoformat()

            try:
                result = await task_handler(task.input_payload)
                task.result = result
                task.status = "completed"
            except Exception as exc:
                task.error = str(exc)
                task.status = "failed"
            finally:
                task.completed_at = datetime.now(timezone.utc).isoformat()

    await asyncio.gather(*[_run_one(t) for t in job.tasks])

    job.status = "aggregating"
    return job


def aggregate_results(
    job_id: str,
    strategy: str = "merge",  # merge / best / vote / average
) -> Dict[str, Any]:
    """
    Fan-in: aggregate task results.
    Strategies:
    - merge: combine all results into a list
    - best: pick the result with highest 'score' field
    - vote: majority vote on categorical outputs
    - average: average numerical outputs
    """
    job = _swarm_jobs.get(job_id)
    if not job:
        raise ValueError(f"Swarm job {job_id} not found")

    completed = [t for t in job.tasks if t.status == "completed" and t.result]
    failed = [t for t in job.tasks if t.status == "failed"]

    if not completed:
        job.aggregated_result = {"success": False, "error": "All tasks failed", "failed_count": len(failed)}
        job.status = "failed"
        return job.aggregated_result

    if strategy == "merge":
        aggregated = {"results": [t.result for t in completed], "count": len(completed)}
    elif strategy == "best":
        best = max(completed, key=lambda t: t.result.get("score", 0) if t.result else 0)
        aggregated = {"best_result": best.result, "best_task_id": best.task_id}
    elif strategy == "vote":
        from collections import Counter
        votes = Counter(str(t.result) for t in completed)
        winner, count = votes.most_common(1)[0]
        aggregated = {"winner": winner, "vote_count": count, "total": len(completed)}
    elif strategy == "average":
        # Simple average of numeric fields
        keys: set[str] = set()
        for t in completed:
            if t.result:
                keys.update(t.result.keys())
        avg: dict[str, float] = {}
        for k in keys:
            vals = [t.result[k] for t in completed if t.result and isinstance(t.result.get(k), (int, float))]
            if vals:
                avg[k] = sum(vals) / len(vals)
        aggregated = {"averages": avg, "count": len(completed)}
    else:
        aggregated = {"results": [t.result for t in completed], "count": len(completed)}

    job.aggregated_result = {
        "success": True,
        "strategy": strategy,
        "completed_count": len(completed),
        "failed_count": len(failed),
        "aggregated": aggregated,
    }
    job.status = "completed"
    job.completed_at = datetime.now(timezone.utc).isoformat()
    return job.aggregated_result
