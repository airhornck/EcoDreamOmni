"""Publish task models and in-memory store."""

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class PublishTask:
    id: str
    draft_id: str
    account_id: str
    platform: str
    status: str  # pending, scheduled, publishing, published, failed, cancelled, skipped
    scheduled_at: Optional[str] = None
    published_at: Optional[str] = None
    published_url: Optional[str] = None
    platform_post_id: Optional[str] = None
    error_reason: Optional[str] = None
    publish_skipped_reason: Optional[str] = None
    retry_count: int = 0
    created_at: str = ""
    updated_at: str = ""
    task_hub_task_id: Optional[str] = None
    created_by: Optional[str] = None


_task_db: Dict[str, PublishTask] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_task(
    draft_id: str,
    account_id: str,
    platform: str,
    scheduled_at: Optional[str] = None,
    task_hub_task_id: Optional[str] = None,
    created_by: Optional[str] = None,
) -> PublishTask:
    task_id = secrets.token_urlsafe(16)
    now = _now()
    task = PublishTask(
        id=task_id,
        draft_id=draft_id,
        account_id=account_id,
        platform=platform,
        status="pending",
        scheduled_at=scheduled_at,
        created_at=now,
        updated_at=now,
        task_hub_task_id=task_hub_task_id,
        created_by=created_by,
    )
    _task_db[task_id] = task
    return task


def get_task(task_id: str) -> Optional[PublishTask]:
    return _task_db.get(task_id)


def list_tasks(created_by: Optional[str] = None) -> List[PublishTask]:
    tasks = list(_task_db.values())
    if created_by:
        tasks = [t for t in tasks if t.created_by == created_by]
    return tasks


def update_task(task_id: str, **kwargs) -> Optional[PublishTask]:
    task = _task_db.get(task_id)
    if task is None:
        return None
    for key, value in kwargs.items():
        if hasattr(task, key):
            setattr(task, key, value)
    task.updated_at = _now()
    return task


def delete_task(task_id: str) -> bool:
    if task_id in _task_db:
        del _task_db[task_id]
        return True
    return False


def clear_tasks() -> None:
    _task_db.clear()
