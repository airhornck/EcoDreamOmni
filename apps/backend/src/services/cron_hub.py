"""CronHub — Job Registry、Schedule Engine、Execution Runner、Retry & DLQ.

Aligned with detailed design §6 / PRD V2.5 §9.
Open-source: croniter (Cron parsing), stamina (retry logic simulated).
"""

import secrets
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    from croniter import croniter
except ImportError:  # pragma: no cover
    croniter = None  # type: ignore


class JobType(str, Enum):
    SYSTEM = "SYSTEM"
    CUSTOM = "CUSTOM"


class TargetType(str, Enum):
    AGENT = "AGENT"
    API = "API"
    SCRIPT = "SCRIPT"


class ConcurrencyPolicy(str, Enum):
    SKIP = "SKIP"
    QUEUE = "QUEUE"
    ALLOW = "ALLOW"


class JobStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"


class ExecutionType(str, Enum):
    SCHEDULED = "SCHEDULED"
    MANUAL = "MANUAL"
    DRY_RUN = "DRY_RUN"
    RETRY = "RETRY"


class ExecutionStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"


class ErrorType(str, Enum):
    RETRYABLE = "RETRYABLE"
    NON_RETRYABLE = "NON_RETRYABLE"
    AGENT_DEGRADED = "AGENT_DEGRADED"


class DeadLetterStatus(str, Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    RETRIED = "RETRIED"
    IGNORED = "IGNORED"
    MANUAL_EXECUTED = "MANUAL_EXECUTED"


# ─── Dataclasses ───

@dataclass
class CronJob:
    id: str
    name: str
    description: str
    job_type: JobType
    source_template: Optional[str]
    target_type: TargetType
    target_id: str
    target_params: Dict[str, Any]
    schedule: str
    timezone: str
    concurrency_policy: ConcurrencyPolicy
    retry_policy: Dict[str, Any]
    timeout_seconds: int
    dry_run_supported: bool
    status: JobStatus
    owner: str
    current_version: int
    created_at: str
    updated_at: str


@dataclass
class JobExecution:
    id: str
    job_id: str
    version: int
    execution_type: ExecutionType
    scheduled_at: str
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    duration_ms: Optional[int] = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    output_summary: Optional[str] = None
    error_message: Optional[str] = None
    error_type: Optional[ErrorType] = None
    retry_count: int = 0
    trace_id: str = ""
    triggered_by: Optional[str] = None
    created_at: str = ""


@dataclass
class DeadLetterJob:
    id: str
    job_id: str
    execution_id: str
    failed_at: str
    error_message: str
    error_type: ErrorType
    retry_exhausted: bool
    context_snapshot: Dict[str, Any]
    status: DeadLetterStatus
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    created_at: str = ""


# ─── In-memory stores ───
_job_db: Dict[str, CronJob] = {}
_execution_db: List[JobExecution] = []
_dlq_db: List[DeadLetterJob] = []
_locks: Dict[str, str] = {}  # job_id → execution_id (distributed lock simulation)
_lock_mutex = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(8)}"


# ─── Cron parsing (croniter) ───

def validate_cron(expression: str) -> bool:
    """Validate cron expression using croniter."""
    if croniter is None:
        # Fallback: basic 5-field check
        parts = expression.split()
        return len(parts) == 5
    try:
        croniter(expression)
        return True
    except (ValueError, KeyError):
        return False


def get_next_run(expression: str, timezone_str: str = "Asia/Shanghai") -> Optional[str]:
    """Return ISO datetime string of next execution."""
    if croniter is None:
        return None
    try:
        # Use UTC for simplicity in tests; real implementation would use pytz
        itr = croniter(expression, datetime.now(timezone.utc))
        nxt = itr.get_next(datetime)
        return nxt.isoformat()
    except Exception:
        return None


def get_run_times_in_range(
    expression: str,
    start: datetime,
    end: datetime,
) -> List[str]:
    """Return all execution times within a range."""
    if croniter is None:
        return []
    runs: List[str] = []
    itr = croniter(expression, start)
    while True:
        nxt = itr.get_next(datetime)
        if nxt > end:
            break
        runs.append(nxt.isoformat())
    return runs


# ─── Job Registry ───

def create_job(
    name: str,
    target_type: str,
    target_id: str,
    schedule: str,
    *,
    description: str = "",
    job_type: str = "CUSTOM",
    source_template: Optional[str] = None,
    target_params: Optional[Dict[str, Any]] = None,
    timezone: str = "Asia/Shanghai",
    concurrency_policy: str = "SKIP",
    retry_policy: Optional[Dict[str, Any]] = None,
    timeout_seconds: int = 300,
    dry_run_supported: bool = False,
    owner: str = "",
) -> CronJob:
    if not validate_cron(schedule):
        raise ValueError(f"Invalid cron expression: {schedule}")
    job_id = _new_id("job")
    now = _now()
    job = CronJob(
        id=job_id,
        name=name,
        description=description,
        job_type=JobType(job_type),
        source_template=source_template,
        target_type=TargetType(target_type),
        target_id=target_id,
        target_params=target_params or {},
        schedule=schedule,
        timezone=timezone,
        concurrency_policy=ConcurrencyPolicy(concurrency_policy),
        retry_policy=retry_policy or {"max_retries": 3, "backoff_type": "exponential", "initial_delay_sec": 60},
        timeout_seconds=timeout_seconds,
        dry_run_supported=dry_run_supported,
        status=JobStatus.ACTIVE,
        owner=owner,
        current_version=1,
        created_at=now,
        updated_at=now,
    )
    _job_db[job_id] = job
    return job


def get_job(job_id: str) -> Optional[CronJob]:
    return _job_db.get(job_id)


def list_jobs(
    status: Optional[str] = None,
    job_type: Optional[str] = None,
) -> List[CronJob]:
    results = list(_job_db.values())
    if status:
        results = [j for j in results if j.status.value == status]
    if job_type:
        results = [j for j in results if j.job_type.value == job_type]
    return results


def update_job(job_id: str, **kwargs) -> Optional[CronJob]:
    job = _job_db.get(job_id)
    if not job:
        return None
    for key, value in kwargs.items():
        if hasattr(job, key):
            if key == "status":
                value = JobStatus(value)
            elif key == "concurrency_policy":
                value = ConcurrencyPolicy(value)
            setattr(job, key, value)
    job.updated_at = _now()
    return job


def delete_job(job_id: str) -> bool:
    return _job_db.pop(job_id, None) is not None


# ─── Distributed Lock (Redis SET NX simulation) ───

def acquire_lock(job_id: str, execution_id: str, ttl_seconds: int = 600) -> bool:
    """Try to acquire a lock for the job. Returns True if acquired."""
    with _lock_mutex:
        if job_id in _locks:
            return False
        _locks[job_id] = execution_id
        return True


def release_lock(job_id: str, execution_id: str) -> bool:
    """Release the lock if held by the given execution."""
    with _lock_mutex:
        if _locks.get(job_id) == execution_id:
            del _locks[job_id]
            return True
        return False


def is_locked(job_id: str) -> bool:
    with _lock_mutex:
        return job_id in _locks


# ─── Execution Runner ───

def execute_job(
    job_id: str,
    execution_type: str = "MANUAL",
    triggered_by: Optional[str] = None,
) -> JobExecution:
    job = _job_db.get(job_id)
    if not job:
        raise ValueError(f"Job not found: {job_id}")

    exec_id = _new_id("exec")
    now = _now()

    # Concurrency check
    if job.concurrency_policy == ConcurrencyPolicy.SKIP and is_locked(job_id):
        execution = JobExecution(
            id=exec_id,
            job_id=job_id,
            version=job.current_version,
            execution_type=ExecutionType(execution_type),
            scheduled_at=now,
            status=ExecutionStatus.SKIPPED,
            output_summary="Skipped due to concurrency policy",
            trace_id=_new_id("trace"),
            triggered_by=triggered_by,
            created_at=now,
        )
        _execution_db.append(execution)
        return execution

    # Date range check (for custom cron with date range)
    params = job.target_params or {}
    start_str = params.get("date_range_start")
    end_str = params.get("date_range_end")
    if start_str or end_str:
        from datetime import date
        today = date.today().isoformat()
        if start_str and today < start_str:
            execution = JobExecution(
                id=exec_id,
                job_id=job_id,
                version=job.current_version,
                execution_type=ExecutionType(execution_type),
                scheduled_at=now,
                status=ExecutionStatus.SKIPPED,
                output_summary=f"Skipped: before date range start ({start_str})",
                trace_id=_new_id("trace"),
                triggered_by=triggered_by,
                created_at=now,
            )
            _execution_db.append(execution)
            return execution
        if end_str and today > end_str:
            execution = JobExecution(
                id=exec_id,
                job_id=job_id,
                version=job.current_version,
                execution_type=ExecutionType(execution_type),
                scheduled_at=now,
                status=ExecutionStatus.SKIPPED,
                output_summary=f"Skipped: after date range end ({end_str})",
                trace_id=_new_id("trace"),
                triggered_by=triggered_by,
                created_at=now,
            )
            _execution_db.append(execution)
            return execution

    acquire_lock(job_id, exec_id, ttl_seconds=job.timeout_seconds * 2)

    execution = JobExecution(
        id=exec_id,
        job_id=job_id,
        version=job.current_version,
        execution_type=ExecutionType(execution_type),
        scheduled_at=now,
        started_at=now,
        status=ExecutionStatus.RUNNING,
        trace_id=_new_id("trace"),
        triggered_by=triggered_by,
        created_at=now,
    )
    _execution_db.append(execution)
    return execution


def complete_execution(
    execution_id: str,
    status: str,
    output_summary: Optional[str] = None,
    error_message: Optional[str] = None,
    error_type: Optional[str] = None,
) -> Optional[JobExecution]:
    for ex in _execution_db:
        if ex.id == execution_id:
            ex.status = ExecutionStatus(status)
            ex.ended_at = _now()
            if ex.started_at:
                started = datetime.fromisoformat(ex.started_at)
                ended = datetime.fromisoformat(ex.ended_at)
                ex.duration_ms = int((ended - started).total_seconds() * 1000)
            ex.output_summary = output_summary
            ex.error_message = error_message
            if error_type:
                ex.error_type = ErrorType(error_type)
            release_lock(ex.job_id, execution_id)
            return ex
    return None


def list_executions(
    job_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
) -> List[JobExecution]:
    results = _execution_db[:]
    if job_id:
        results = [e for e in results if e.job_id == job_id]
    if status:
        results = [e for e in results if e.status.value == status]
    return results[-limit:]


# ─── Retry & DLQ ───

def retry_execution(execution_id: str) -> Optional[JobExecution]:
    """Retry a failed execution according to its job's retry policy."""
    for ex in _execution_db:
        if ex.id == execution_id:
            job = _job_db.get(ex.job_id)
            if not job:
                return None
            max_retries = job.retry_policy.get("max_retries", 3)
            if ex.retry_count >= max_retries:
                # Move to DLQ
                _move_to_dlq(ex, retry_exhausted=True)
                return None
            ex.retry_count += 1
            ex.status = ExecutionStatus.PENDING
            ex.error_message = None
            ex.error_type = None
            ex.started_at = None
            ex.ended_at = None
            ex.duration_ms = None
            return ex
    return None


def _move_to_dlq(execution: JobExecution, retry_exhausted: bool = True) -> DeadLetterJob:
    dlq = DeadLetterJob(
        id=_new_id("dlq"),
        job_id=execution.job_id,
        execution_id=execution.id,
        failed_at=_now(),
        error_message=execution.error_message or "Unknown error",
        error_type=execution.error_type or ErrorType.RETRYABLE,
        retry_exhausted=retry_exhausted,
        context_snapshot={
            "target_type": _job_db.get(execution.job_id, {}).target_type.value if _job_db.get(execution.job_id) else None,
            "target_id": _job_db.get(execution.job_id, {}).target_id if _job_db.get(execution.job_id) else None,
            "target_params": _job_db.get(execution.job_id, {}).target_params if _job_db.get(execution.job_id) else {},
            "retry_count": execution.retry_count,
        },
        status=DeadLetterStatus.PENDING_REVIEW,
        created_at=_now(),
    )
    _dlq_db.append(dlq)
    release_lock(execution.job_id, execution.id)
    return dlq


def list_dlq(
    job_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
) -> List[DeadLetterJob]:
    results = _dlq_db[:]
    if job_id:
        results = [d for d in results if d.job_id == job_id]
    if status:
        results = [d for d in results if d.status.value == status]
    return results[-limit:]


def review_dlq(
    dlq_id: str,
    decision: str,
    reviewed_by: str,
) -> Optional[DeadLetterJob]:
    for dlq in _dlq_db:
        if dlq.id == dlq_id:
            dlq.status = DeadLetterStatus(decision)
            dlq.reviewed_by = reviewed_by
            dlq.reviewed_at = _now()
            return dlq
    return None


def retry_dlq(dlq_id: str) -> Optional[DeadLetterJob]:
    for dlq in _dlq_db:
        if dlq.id == dlq_id:
            ex = retry_execution(dlq.execution_id)
            if ex:
                _dlq_db.remove(dlq)
                return dlq
            return None
    return None


def delete_dlq(dlq_id: str) -> bool:
    for dlq in _dlq_db:
        if dlq.id == dlq_id:
            _dlq_db.remove(dlq)
            return True
    return False


# ─── Clear stores (for testing) ───

def _clear_stores():
    _job_db.clear()
    _execution_db.clear()
    _dlq_db.clear()
    with _lock_mutex:
        _locks.clear()
