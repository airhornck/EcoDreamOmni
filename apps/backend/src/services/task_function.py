"""Task Function layer — DB operations for TaskORM.

All direct database access for Task entities lives here.
Agent layer (task_hub.py) MUST NOT import TaskORM or use db sessions directly.
"""

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from src.models.task_orm import TaskORM


class TaskStatus(str, Enum):
    DRAFT = "draft"
    CONFIGURING = "configuring"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    HUMAN_WAIT = "human_wait"
    APPROVED_WAITING_PUBLISH = "approved_waiting_publish"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class HumanDecision(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REVISE = "REVISE"


# ─── Valid state transitions ───
_TRANSITIONS = {
    TaskStatus.DRAFT: {TaskStatus.CONFIGURING, TaskStatus.HUMAN_WAIT, TaskStatus.CANCELLED},
    TaskStatus.CONFIGURING: {TaskStatus.QUEUED, TaskStatus.CANCELLED},
    TaskStatus.QUEUED: {TaskStatus.RUNNING, TaskStatus.FAILED, TaskStatus.CANCELLED},
    TaskStatus.RUNNING: {TaskStatus.PAUSED, TaskStatus.HUMAN_WAIT, TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED},
    TaskStatus.PAUSED: {TaskStatus.RUNNING, TaskStatus.CANCELLED},
    TaskStatus.HUMAN_WAIT: {TaskStatus.RUNNING, TaskStatus.FAILED, TaskStatus.APPROVED_WAITING_PUBLISH, TaskStatus.CONFIGURING},
    TaskStatus.APPROVED_WAITING_PUBLISH: {TaskStatus.RUNNING, TaskStatus.CONFIGURING, TaskStatus.DRAFT, TaskStatus.CANCELLED},
    TaskStatus.FAILED: {TaskStatus.QUEUED},
    TaskStatus.COMPLETED: set(),
    TaskStatus.CANCELLED: set(),
}


# ─── Dataclasses ───

@dataclass
class Task:
    id: str
    name: str
    workflow_template_id: Optional[str]
    workflow_version: int
    account_id: str
    persona_id: str
    prompt_variables: Dict[str, Any]
    status: TaskStatus
    current_node_index: int
    parent_task_id: Optional[str]
    priority: int
    scheduled_at: Optional[str]
    created_by: str
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None
    workflow_template_name: Optional[str] = None
    account_name: Optional[str] = None
    persona_name: Optional[str] = None
    current_step_label: Optional[str] = None
    estimated_completion_at: Optional[str] = None
    platform: str = "xhs"
    content_format: Optional[str] = None
    persona_story_id: Optional[str] = None
    story_name: Optional[str] = None
    node_id: Optional[str] = None
    content_series_id: Optional[str] = None
    content_series_name: Optional[str] = None
    review_decision: Optional[str] = None
    reviewed_at: Optional[str] = None
    reviewer: Optional[str] = None
    review_reason: Optional[str] = None
    publish_confirmed_at: Optional[str] = None
    publish_confirmer: Optional[str] = None
    cron_job_id: Optional[str] = None
    trace_id: Optional[str] = None
    execution_id: Optional[str] = None
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    agent_config_snapshot: Dict[str, Any] = field(default_factory=dict)
    content_strategy: Optional[Dict[str, Any]] = None
    methodology_stage_id: Optional[str] = None
    timeline_event_id: Optional[str] = None
    # ── Publish audit fields (P0 Fix: persist publish results) ──
    published_url: Optional[str] = None
    platform_post_id: Optional[str] = None
    published_at: Optional[str] = None
    publish_error: Optional[str] = None


@dataclass
class TaskNodeExecution:
    id: str
    task_id: str
    node_id: str
    node_type: str
    agent_id: Optional[str]
    prompt_template_id: Optional[str]
    status: str
    input_context: Dict[str, Any]
    output_context: Dict[str, Any]
    started_at: Optional[str]
    ended_at: Optional[str]
    duration_ms: Optional[int]
    error_message: Optional[str]
    trace_id: str
    human_decision: Optional[str]
    human_feedback: Optional[str]
    created_at: str


# ─── In-memory caches (managed by Function layer) ───
_task_db: Dict[str, Task] = {}
_node_exec_db: List[TaskNodeExecution] = []


# ─── Helpers ───

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(8)}"


def _can_transition(current: TaskStatus, target: TaskStatus) -> bool:
    return target in _TRANSITIONS.get(current, set())


def _iso_or_none(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


def _db_to_task(orm: TaskORM) -> Task:
    """Convert ORM object to domain Task dataclass."""
    return Task(
        id=str(orm.id),
        name=orm.name,
        workflow_template_id=orm.workflow_template_id,
        workflow_version=orm.workflow_version,
        account_id=orm.account_id,
        persona_id=orm.persona_id,
        persona_story_id=orm.persona_story_id,
        node_id=orm.node_id,
        content_series_id=orm.content_series_id,
        prompt_variables=orm.prompt_variables or {},
        status=TaskStatus(orm.status),
        current_node_index=orm.current_node_index,
        parent_task_id=orm.parent_task_id,
        priority=orm.priority,
        scheduled_at=_iso_or_none(orm.scheduled_at),
        created_by=orm.created_by,
        platform=orm.platform,
        content_format=orm.content_format,
        review_decision=orm.review_decision,
        reviewed_at=_iso_or_none(orm.reviewed_at),
        reviewer=orm.reviewer,
        review_reason=orm.review_reason,
        publish_confirmed_at=_iso_or_none(orm.publish_confirmed_at),
        publish_confirmer=orm.publish_confirmer,
        cron_job_id=orm.cron_job_id,
        trace_id=orm.trace_id,
        execution_id=orm.execution_id,
        created_at=_iso_or_none(orm.created_at) or _now(),
        updated_at=_iso_or_none(orm.updated_at) or _now(),
        completed_at=_iso_or_none(orm.completed_at),
        agent_id=orm.agent_id,
        agent_config_snapshot=orm.agent_config_snapshot or {},
        content_strategy=orm.content_strategy,
        methodology_stage_id=orm.methodology_stage_id,
        timeline_event_id=str(orm.timeline_event_id) if orm.timeline_event_id else None,
        # ── Publish audit fields (P0 Fix) ──
        published_url=orm.published_url,
        platform_post_id=orm.platform_post_id,
        published_at=_iso_or_none(orm.published_at),
        publish_error=orm.publish_error,
    )


def _task_to_orm(task: Task) -> TaskORM:
    """Convert domain Task dataclass to ORM object (for inserts)."""
    return TaskORM(
        id=task.id if len(task.id) == 36 else None,
        name=task.name,
        workflow_template_id=task.workflow_template_id,
        workflow_version=task.workflow_version,
        account_id=task.account_id,
        persona_id=task.persona_id,
        persona_story_id=task.persona_story_id,
        node_id=task.node_id,
        content_series_id=task.content_series_id,
        platform=task.platform,
        content_format=task.content_format,
        status=task.status.value,
        priority=task.priority,
        current_node_index=task.current_node_index,
        prompt_variables=task.prompt_variables,
        parent_task_id=task.parent_task_id,
        scheduled_at=datetime.fromisoformat(task.scheduled_at) if task.scheduled_at else None,
        created_by=task.created_by,
        review_decision=task.review_decision,
        reviewed_at=datetime.fromisoformat(task.reviewed_at) if task.reviewed_at else None,
        reviewer=task.reviewer,
        review_reason=task.review_reason,
        publish_confirmed_at=datetime.fromisoformat(task.publish_confirmed_at) if task.publish_confirmed_at else None,
        publish_confirmer=task.publish_confirmer,
        cron_job_id=task.cron_job_id,
        trace_id=task.trace_id,
        execution_id=task.execution_id,
        created_at=datetime.fromisoformat(task.created_at) if task.created_at else datetime.now(timezone.utc),
        updated_at=datetime.fromisoformat(task.updated_at) if task.updated_at else datetime.now(timezone.utc),
        completed_at=datetime.fromisoformat(task.completed_at) if task.completed_at else None,
        agent_id=task.agent_id,
        agent_config_snapshot=task.agent_config_snapshot,
        content_strategy=task.content_strategy,
        methodology_stage_id=task.methodology_stage_id,
        timeline_event_id=UUID(task.timeline_event_id) if task.timeline_event_id else None,
        # ── Publish audit fields (P0 Fix) ──
        published_url=task.published_url,
        platform_post_id=task.platform_post_id,
        published_at=datetime.fromisoformat(task.published_at) if task.published_at else None,
        publish_error=task.publish_error,
    )


def _update_orm_from_task(orm: TaskORM, task: Task) -> None:
    """Update an existing ORM object from a Task dataclass."""
    orm.name = task.name
    orm.workflow_template_id = task.workflow_template_id
    orm.workflow_version = task.workflow_version
    orm.account_id = task.account_id
    orm.persona_id = task.persona_id
    orm.persona_story_id = task.persona_story_id
    orm.node_id = task.node_id
    orm.content_series_id = task.content_series_id
    orm.platform = task.platform
    orm.content_format = task.content_format
    orm.status = task.status.value
    orm.priority = task.priority
    orm.current_node_index = task.current_node_index
    orm.prompt_variables = task.prompt_variables
    orm.parent_task_id = task.parent_task_id
    orm.scheduled_at = datetime.fromisoformat(task.scheduled_at) if task.scheduled_at else None
    orm.created_by = task.created_by
    orm.review_decision = task.review_decision
    orm.reviewed_at = datetime.fromisoformat(task.reviewed_at) if task.reviewed_at else None
    orm.reviewer = task.reviewer
    orm.review_reason = task.review_reason
    orm.publish_confirmed_at = datetime.fromisoformat(task.publish_confirmed_at) if task.publish_confirmed_at else None
    orm.publish_confirmer = task.publish_confirmer
    orm.cron_job_id = task.cron_job_id
    orm.trace_id = task.trace_id
    orm.execution_id = task.execution_id
    orm.updated_at = datetime.now(timezone.utc)
    orm.completed_at = datetime.fromisoformat(task.completed_at) if task.completed_at else None
    orm.agent_id = task.agent_id
    orm.agent_config_snapshot = task.agent_config_snapshot
    orm.content_strategy = task.content_strategy
    orm.methodology_stage_id = task.methodology_stage_id
    orm.timeline_event_id = UUID(task.timeline_event_id) if task.timeline_event_id else None
    # ── Publish audit fields (P0 Fix) ──
    orm.published_url = task.published_url
    orm.platform_post_id = task.platform_post_id
    orm.published_at = datetime.fromisoformat(task.published_at) if task.published_at else None
    orm.publish_error = task.publish_error


# ─── Cache access (for Agent layer) ───

def get_task_cache(task_id: str) -> Optional[Task]:
    # Phase 4: In-memory cache disabled to ensure data isolation by creator.
    # All reads go directly to PostgreSQL.
    return None


def set_task_cache(task: Task) -> None:
    pass


def pop_task_cache(task_id: str) -> None:
    pass


def list_task_cache() -> List[Task]:
    # Phase 4: In-memory cache disabled to ensure data isolation by creator.
    return []


def clear_task_cache() -> None:
    _task_db.clear()


# ─── CRUD ───

async def load_tasks_into_cache(db: AsyncSession) -> int:
    """Warm the L1 cache from PostgreSQL. Call on startup.

    Phase 4: Cache warming is disabled. All reads go directly to DB.
    """
    return 0


async def create_task_in_db(
    db: AsyncSession,
    task: Task,
) -> Task:
    """Persist a Task dataclass to DB and update cache."""
    orm = _task_to_orm(task)
    db.add(orm)
    await db.commit()
    await db.refresh(orm)
    task.id = str(orm.id)
    return task


async def get_task_from_db(db: AsyncSession, task_id: str) -> Optional[Task]:
    """Fetch task from DB, bypass cache."""
    try:
        from uuid import UUID as UUID_CLS
        UUID_CLS(task_id)
    except ValueError:
        return None
    result = await db.execute(select(TaskORM).where(TaskORM.id == task_id))
    orm = result.scalar_one_or_none()
    if orm:
        task = _db_to_task(orm)
        return task
    return None


async def list_tasks_from_db(
    db: AsyncSession,
    status: Optional[str] = None,
    account_id: Optional[str] = None,
    parent_task_id: Optional[str] = None,
    created_by: Optional[str] = None,
) -> List[Task]:
    query = select(TaskORM).order_by(TaskORM.created_at.desc())
    if status:
        query = query.where(TaskORM.status == status)
    if account_id:
        query = query.where(TaskORM.account_id == account_id)
    if parent_task_id:
        query = query.where(TaskORM.parent_task_id == parent_task_id)
    if created_by:
        query = query.where(TaskORM.created_by == created_by)

    result = await db.execute(query)
    orms = result.scalars().all()
    tasks = [_db_to_task(o) for o in orms]
    return tasks


async def update_task_in_db(
    db: AsyncSession,
    task_id: str,
    task: Task,
) -> Optional[Task]:
    """Update an existing task in DB from a Task dataclass."""
    result = await db.execute(select(TaskORM).where(TaskORM.id == task_id))
    orm = result.scalar_one_or_none()
    if not orm:
        return None
    _update_orm_from_task(orm, task)
    await db.commit()
    await db.refresh(orm)
    return task


async def transition_task_in_db(
    db: AsyncSession,
    task_id: str,
    new_status: str,
) -> Optional[Task]:
    """Transition task status with validation."""
    result = await db.execute(select(TaskORM).where(TaskORM.id == task_id))
    orm = result.scalar_one_or_none()
    if not orm:
        return None

    task = _db_to_task(orm)
    target = TaskStatus(new_status)
    if not _can_transition(task.status, target):
        raise ValueError(f"Invalid transition: {task.status.value} -> {target.value}")
    task.status = target
    task.updated_at = _now()
    if target in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
        task.completed_at = _now()

    _update_orm_from_task(orm, task)
    await db.commit()
    await db.refresh(orm)
    return task


async def delete_task_from_db(db: AsyncSession, task_id: str) -> bool:
    result = await db.execute(select(TaskORM).where(TaskORM.id == task_id))
    orm = result.scalar_one_or_none()
    if not orm:
        return False
    await db.delete(orm)
    await db.commit()
    return True
