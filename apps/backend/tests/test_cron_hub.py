"""Tests for CronHub (Phase 2 / PRD V2.5 §9).

Red-Green TDD for:
  - Job registration with cron validation
  - Cron parsing (next run, range)
  - Distributed lock (acquire/release)
  - Execution runner (start/complete/skip)
  - Retry logic & DLQ
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.services import cron_hub as ch
from src.services.cron_hub import (
    JobType, TargetType, ConcurrencyPolicy, JobStatus,
    ExecutionType, ExecutionStatus, ErrorType, DeadLetterStatus,
)


@pytest.fixture(autouse=True)
def clear_db():
    ch._clear_stores()
    yield


# ─── 1. Job Registration ───

def test_create_job():
    job = ch.create_job(
        name="Daily Content Generation",
        target_type="AGENT",
        target_id="content-forge-001",
        schedule="0 9 * * *",
        owner="alice",
    )
    assert job.id.startswith("job_")
    assert job.name == "Daily Content Generation"
    assert job.status == JobStatus.ACTIVE
    assert job.schedule == "0 9 * * *"


def test_create_job_invalid_cron():
    with pytest.raises(ValueError):
        ch.create_job(
            name="Bad Job",
            target_type="AGENT",
            target_id="x",
            schedule="not-a-cron",
        )


def test_list_jobs_filter():
    ch.create_job("J1", "AGENT", "a1", "0 9 * * *", job_type="SYSTEM")
    ch.create_job("J2", "API", "a2", "0 10 * * *", job_type="CUSTOM")
    systems = ch.list_jobs(job_type="SYSTEM")
    assert len(systems) == 1
    assert systems[0].name == "J1"


# ─── 2. Cron Parsing ───

def test_validate_cron_valid():
    assert ch.validate_cron("0 9 * * *") is True
    assert ch.validate_cron("*/5 * * * *") is True


def test_validate_cron_invalid():
    assert ch.validate_cron("invalid") is False


def test_get_next_run():
    nxt = ch.get_next_run("0 0 * * *")
    assert nxt is not None
    dt = datetime.fromisoformat(nxt)
    assert dt.hour == 0
    assert dt.minute == 0


def test_get_run_times_in_range():
    start = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 3, 0, 0, tzinfo=timezone.utc)
    runs = ch.get_run_times_in_range("0 0 * * *", start, end)
    # Should get 2026-01-01 00:00 and 2026-01-02 00:00
    assert len(runs) >= 2


# ─── 3. Distributed Lock ───

def test_acquire_and_release_lock():
    assert ch.acquire_lock("job_001", "exec_001", ttl_seconds=60) is True
    assert ch.is_locked("job_001") is True
    # Second acquire should fail
    assert ch.acquire_lock("job_001", "exec_002", ttl_seconds=60) is False
    # Release with wrong execution should fail
    assert ch.release_lock("job_001", "exec_002") is False
    # Release with correct execution should succeed
    assert ch.release_lock("job_001", "exec_001") is True
    assert ch.is_locked("job_001") is False


def test_lock_isolated_per_job():
    assert ch.acquire_lock("job_A", "exec_A") is True
    assert ch.acquire_lock("job_B", "exec_B") is True
    assert ch.is_locked("job_A") is True
    assert ch.is_locked("job_B") is True


# ─── 4. Execution Runner ───

def test_execute_job():
    job = ch.create_job("Test", "AGENT", "a1", "0 * * * *")
    ex = ch.execute_job(job.id, execution_type="MANUAL", triggered_by="alice")
    assert ex.status == ExecutionStatus.RUNNING
    assert ex.job_id == job.id
    assert ch.is_locked(job.id) is True


def test_execute_job_concurrency_skip():
    job = ch.create_job("Test", "AGENT", "a1", "0 * * * *", concurrency_policy="SKIP")
    ex1 = ch.execute_job(job.id)
    assert ex1.status == ExecutionStatus.RUNNING
    ex2 = ch.execute_job(job.id)
    assert ex2.status == ExecutionStatus.SKIPPED


def test_execute_job_concurrency_allow():
    job = ch.create_job("Test", "AGENT", "a1", "0 * * * *", concurrency_policy="ALLOW")
    ex1 = ch.execute_job(job.id)
    ex2 = ch.execute_job(job.id)
    assert ex1.status == ExecutionStatus.RUNNING
    assert ex2.status == ExecutionStatus.RUNNING


def test_complete_execution_success():
    job = ch.create_job("Test", "AGENT", "a1", "0 * * * *")
    ex = ch.execute_job(job.id)
    completed = ch.complete_execution(ex.id, "SUCCESS", output_summary="Done")
    assert completed is not None
    assert completed.status == ExecutionStatus.SUCCESS
    assert completed.output_summary == "Done"
    assert completed.ended_at is not None
    assert completed.duration_ms is not None
    assert ch.is_locked(job.id) is False


def test_complete_execution_failure():
    job = ch.create_job("Test", "AGENT", "a1", "0 * * * *")
    ex = ch.execute_job(job.id)
    completed = ch.complete_execution(
        ex.id, "FAILED",
        error_message="Connection timeout",
        error_type="RETRYABLE",
    )
    assert completed.status == ExecutionStatus.FAILED
    assert completed.error_type == ErrorType.RETRYABLE


# ─── 5. Retry Logic ───

def test_retry_execution():
    job = ch.create_job("Test", "AGENT", "a1", "0 * * * *", retry_policy={"max_retries": 2})
    ex = ch.execute_job(job.id)
    ch.complete_execution(ex.id, "FAILED", error_type="RETRYABLE")
    retried = ch.retry_execution(ex.id)
    assert retried is not None
    assert retried.retry_count == 1
    assert retried.status == ExecutionStatus.PENDING


def test_retry_exhausted_moves_to_dlq():
    job = ch.create_job("Test", "AGENT", "a1", "0 * * * *", retry_policy={"max_retries": 1})
    ex = ch.execute_job(job.id)
    ch.complete_execution(ex.id, "FAILED", error_type="RETRYABLE")
    # First retry
    retried = ch.retry_execution(ex.id)
    assert retried is not None
    ch.complete_execution(retried.id, "FAILED", error_type="RETRYABLE")
    # Second retry should exhaust and move to DLQ
    result = ch.retry_execution(retried.id)
    assert result is None
    dlq = ch.list_dlq(job_id=job.id)
    assert len(dlq) == 1
    assert dlq[0].retry_exhausted is True
    assert dlq[0].status == DeadLetterStatus.PENDING_REVIEW


# ─── 6. DLQ Review ───

def test_review_dlq():
    job = ch.create_job("Test", "AGENT", "a1", "0 * * * *", retry_policy={"max_retries": 0})
    ex = ch.execute_job(job.id)
    ch.complete_execution(ex.id, "FAILED", error_type="RETRYABLE")
    ch.retry_execution(ex.id)  # Moves to DLQ immediately (max_retries=0)
    dlq = ch.list_dlq()[0]
    reviewed = ch.review_dlq(dlq.id, "IGNORED", "bob")
    assert reviewed is not None
    assert reviewed.status == DeadLetterStatus.IGNORED
    assert reviewed.reviewed_by == "bob"


# ─── 7. List executions ───

def test_list_executions():
    job = ch.create_job("Test", "AGENT", "a1", "0 * * * *")
    ch.execute_job(job.id)
    ch.execute_job(job.id)
    execs = ch.list_executions(job_id=job.id)
    assert len(execs) == 2


# ─── 8. Integration: full job lifecycle ───

def test_full_job_lifecycle():
    # Register job
    job = ch.create_job(
        name="Hourly Data Sync",
        target_type="API",
        target_id="/api/v1/sync",
        schedule="0 * * * *",
        retry_policy={"max_retries": 1, "backoff_type": "exponential"},
        owner="ops",
    )
    assert ch.validate_cron(job.schedule) is True
    nxt = ch.get_next_run(job.schedule)
    assert nxt is not None

    # Execute
    ex = ch.execute_job(job.id, execution_type="MANUAL", triggered_by="ops")
    assert ex.status == ExecutionStatus.RUNNING
    assert ch.is_locked(job.id) is True

    # Complete successfully
    ch.complete_execution(ex.id, "SUCCESS", output_summary="Synced 42 records")
    assert ch.is_locked(job.id) is False

    # Execute again, fail, retry, fail, move to DLQ
    ex2 = ch.execute_job(job.id)
    ch.complete_execution(ex2.id, "FAILED", error_type="RETRYABLE")
    retried = ch.retry_execution(ex2.id)
    assert retried.retry_count == 1
    ch.complete_execution(retried.id, "FAILED", error_type="RETRYABLE")
    ch.retry_execution(retried.id)  # Exhausted

    dlq = ch.list_dlq(job_id=job.id)
    assert len(dlq) == 1
    assert dlq[0].status == DeadLetterStatus.PENDING_REVIEW

    # Review DLQ
    ch.review_dlq(dlq[0].id, "RETRIED", "admin")
    assert ch.list_dlq(status="PENDING_REVIEW") == []


# ─── Date Range Check ───

def test_execute_job_skips_before_date_range():
    """🔴 Job with date_range_start in the future should be SKIPPED."""
    from datetime import date, timedelta
    future = (date.today() + timedelta(days=7)).isoformat()
    job = ch.create_job(
        name="Future Job",
        target_type="API",
        target_id="publish-task",
        schedule="0 20 * * *",
        target_params={"date_range_start": future, "date_range_end": None},
    )
    ex = ch.execute_job(job.id, "SCHEDULED")
    assert ex.status == ExecutionStatus.SKIPPED
    assert "before date range start" in ex.output_summary


def test_execute_job_skips_after_date_range():
    """🔴 Job with date_range_end in the past should be SKIPPED."""
    from datetime import date, timedelta
    past = (date.today() - timedelta(days=7)).isoformat()
    job = ch.create_job(
        name="Past Job",
        target_type="API",
        target_id="publish-task",
        schedule="0 20 * * *",
        target_params={"date_range_start": None, "date_range_end": past},
    )
    ex = ch.execute_job(job.id, "SCHEDULED")
    assert ex.status == ExecutionStatus.SKIPPED
    assert "after date range end" in ex.output_summary


def test_execute_job_runs_within_date_range():
    """🔴 Job with date range covering today should RUN."""
    from datetime import date, timedelta
    start = (date.today() - timedelta(days=3)).isoformat()
    end = (date.today() + timedelta(days=3)).isoformat()
    job = ch.create_job(
        name="Current Job",
        target_type="API",
        target_id="publish-task",
        schedule="0 20 * * *",
        target_params={"date_range_start": start, "date_range_end": end},
    )
    ex = ch.execute_job(job.id, "SCHEDULED")
    assert ex.status == ExecutionStatus.RUNNING


# ─── Celery Scheduled Trigger ───

def test_check_and_execute_cron_jobs_triggers_due_jobs():
    """🔴 check_and_execute_cron_jobs should trigger jobs whose schedule matches current minute."""
    from datetime import datetime, timezone
    from src.services.celery_tasks import check_and_execute_cron_jobs

    # Create a job scheduled for the current minute
    now = datetime.now(timezone.utc)
    schedule = f"{now.minute} {now.hour} {now.day} {now.month} *"
    job = ch.create_job(
        name="Now Job",
        target_type="API",
        target_id="publish-task",
        schedule=schedule,
    )
    result = check_and_execute_cron_jobs()
    assert result["triggered"] >= 1
    executions = ch.list_executions(job_id=job.id)
    assert len(executions) >= 1
    assert executions[-1].status == ExecutionStatus.RUNNING
