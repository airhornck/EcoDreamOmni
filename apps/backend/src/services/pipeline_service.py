"""Pipeline Service — Async task orchestration with BackgroundTasks (MVP).

MVP: Uses FastAPI BackgroundTasks for zero-dependency async execution.
Production: Migrate to Celery + Redis by swapping _task_executor.
"""

import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


@dataclass
class PipelineTask:
    task_id: str
    task_type: str  # publish, data_analysis, model_training, trend_crawl
    payload: Dict[str, Any]
    status: str  # pending, running, completed, failed, cancelled
    result: Optional[Dict] = None
    error_message: Optional[str] = None
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress_percent: int = 0


_task_db: Dict[str, PipelineTask] = {}
_task_handlers: Dict[str, Callable] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def register_task_handler(task_type: str, handler: Callable) -> None:
    """Register a handler function for a task type.

    Handler signature: handler(payload: dict) -> dict
    """
    _task_handlers[task_type] = handler


def submit_task(task_type: str, payload: Dict[str, Any]) -> PipelineTask:
    """Submit a new async task."""
    task_id = f"task_{secrets.token_urlsafe(12)}"
    task = PipelineTask(
        task_id=task_id,
        task_type=task_type,
        payload=payload,
        status="pending",
        created_at=_now(),
    )
    _task_db[task_id] = task
    return task


def get_task(task_id: str) -> Optional[PipelineTask]:
    return _task_db.get(task_id)


def list_tasks(task_type: Optional[str] = None, status: Optional[str] = None) -> List[PipelineTask]:
    tasks = list(_task_db.values())
    if task_type:
        tasks = [t for t in tasks if t.task_type == task_type]
    if status:
        tasks = [t for t in tasks if t.status == status]
    return sorted(tasks, key=lambda t: t.created_at, reverse=True)


def cancel_task(task_id: str) -> bool:
    task = _task_db.get(task_id)
    if task and task.status in ("pending", "running"):
        task.status = "cancelled"
        task.completed_at = _now()
        return True
    return False


def _run_task_sync(task_id: str) -> None:
    """Synchronous task runner (called from BackgroundTasks or Celery)."""
    task = _task_db.get(task_id)
    if not task:
        return
    if task.status == "cancelled":
        return

    task.status = "running"
    task.started_at = _now()

    handler = _task_handlers.get(task.task_type)
    if not handler:
        task.status = "failed"
        task.error_message = f"No handler registered for task type: {task.task_type}"
        task.completed_at = _now()
        return

    try:
        # Simulate progress for MVP
        task.progress_percent = 25
        result = handler(task.payload)
        task.progress_percent = 100
        task.status = "completed"
        task.result = result
        task.completed_at = _now()
    except Exception as e:
        task.status = "failed"
        task.error_message = str(e)
        task.completed_at = _now()


# ─── Default Task Handlers ───


def _handle_publish(payload: Dict) -> Dict:
    """Async publish handler."""
    from src.services.publisher_service import execute_publish

    task_id = payload.get("publish_task_id")
    content = payload.get("content", {})
    updated = execute_publish(task_id, content)
    return {
        "task_id": task_id,
        "status": updated.status,
        "published_url": updated.published_url,
        "platform_post_id": updated.platform_post_id,
    }


def _handle_data_analysis(payload: Dict) -> Dict:
    """Async 24h data report generation."""
    from src.services.data_analyst_service import generate_data_report

    report = generate_data_report(
        account_id=payload["account_id"],
        content_id=payload["content_id"],
        predicted_ces=payload.get("predicted_ces", 0.0),
        predicted_pool=payload.get("predicted_pool", "L2"),
        period=payload.get("period", "24h"),
    )
    return {
        "report_id": report.id,
        "account_id": report.account_id,
        "mape": report.prediction_comparison.get("mape"),
    }


def _handle_model_training(payload: Dict) -> Dict:
    """Async model training."""
    from src.services.prediction_engine import train_baseline_model

    metrics = train_baseline_model()
    return {"metrics": metrics}


def _handle_trend_crawl(payload: Dict) -> Dict:
    """Async trend crawling."""
    from src.services.trend_scout_service import create_trend_report

    report = create_trend_report(
        query=payload.get("query", ""),
        stage_filter=payload.get("stage_filter", ""),
    )
    return {
        "report_id": report.id,
        "query": report.query,
        "result_count": len(report.results),
    }


# Register default handlers
register_task_handler("publish", _handle_publish)
register_task_handler("data_analysis", _handle_data_analysis)
register_task_handler("model_training", _handle_model_training)
register_task_handler("trend_crawl", _handle_trend_crawl)


# ─── Celery Adapter (Production) ───

def run_task_in_background(task_id: str) -> None:
    """Enqueue task execution using Celery + Redis.

    MVP fallback: If Celery is not available, runs synchronously.
    """
    try:
        from src.services.celery_tasks import run_pipeline_task
        run_pipeline_task.delay(task_id)
    except Exception:
        # Fallback: run synchronously (MVP / testing mode)
        _run_task_sync(task_id)


def clear_pipeline() -> None:
    _task_db.clear()
