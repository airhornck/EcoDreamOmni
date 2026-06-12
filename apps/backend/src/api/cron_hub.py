"""CronHub API — Phase 2 / PRD V2.5 §9.

Routes:
  POST /cron-hub/jobs                # Create job
  GET  /cron-hub/jobs                # List jobs
  GET  /cron-hub/jobs/{id}           # Job detail
  PATCH /cron-hub/jobs/{id}          # Update job
  DELETE /cron-hub/jobs/{id}         # Delete job
  POST /cron-hub/jobs/{id}/execute   # Manual execute
  POST /cron-hub/jobs/{id}/dry-run   # Dry run
  GET  /cron-hub/executions          # List executions
  GET  /cron-hub/executions/{id}     # Execution detail
  POST /cron-hub/executions/{id}/retry  # Retry execution
  POST /cron-hub/executions/{id}/complete # Complete execution (internal)
  GET  /cron-hub/dlq                 # List dead letter jobs
  POST /cron-hub/dlq/{id}/review     # Review DLQ
  POST /cron-hub/validate-cron       # Validate cron expression
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.services import cron_hub

router = APIRouter(prefix="/cron-hub", tags=["cron-hub"])


# ─── Schemas ───

class CreateJobRequest(BaseModel):
    name: str
    target_type: str = Field(..., description="AGENT / API / SCRIPT")
    target_id: str
    schedule: str
    description: str = ""
    job_type: str = "CUSTOM"
    source_template: Optional[str] = None
    target_params: Optional[Dict[str, Any]] = None
    timezone: str = "Asia/Shanghai"
    concurrency_policy: str = "SKIP"
    retry_policy: Optional[Dict[str, Any]] = None
    timeout_seconds: int = 300
    dry_run_supported: bool = False
    owner: str = ""


class JobResponse(BaseModel):
    id: str
    name: str
    description: str
    job_type: str
    target_type: str
    target_id: str
    schedule: str
    timezone: str
    concurrency_policy: str
    timeout_seconds: int
    dry_run_supported: bool
    status: str
    owner: str
    created_at: str


class UpdateJobRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    schedule: Optional[str] = None
    concurrency_policy: Optional[str] = None


class ExecuteRequest(BaseModel):
    execution_type: str = "MANUAL"
    triggered_by: Optional[str] = None


class ExecutionResponse(BaseModel):
    id: str
    job_id: str
    version: int
    execution_type: str
    scheduled_at: str
    started_at: Optional[str]
    ended_at: Optional[str]
    duration_ms: Optional[int]
    status: str
    output_summary: Optional[str]
    error_message: Optional[str]
    error_type: Optional[str]
    retry_count: int
    trace_id: str
    triggered_by: Optional[str]


class CompleteExecutionRequest(BaseModel):
    status: str
    output_summary: Optional[str] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None


class DLQResponse(BaseModel):
    id: str
    job_id: str
    execution_id: str
    failed_at: str
    error_message: str
    error_type: str
    retry_exhausted: bool
    status: str
    reviewed_by: Optional[str]
    reviewed_at: Optional[str]


class ReviewDLQRequest(BaseModel):
    decision: str = Field(..., description="RETRIED / IGNORED / MANUAL_EXECUTED")
    reviewed_by: str


class ValidateCronRequest(BaseModel):
    expression: str


class ValidateCronResponse(BaseModel):
    valid: bool
    next_run: Optional[str] = None


# ─── Helpers ───

def _to_job_response(j: cron_hub.CronJob) -> JobResponse:
    return JobResponse(
        id=j.id,
        name=j.name,
        description=j.description,
        job_type=j.job_type.value,
        target_type=j.target_type.value,
        target_id=j.target_id,
        schedule=j.schedule,
        timezone=j.timezone,
        concurrency_policy=j.concurrency_policy.value,
        timeout_seconds=j.timeout_seconds,
        dry_run_supported=j.dry_run_supported,
        status=j.status.value,
        owner=j.owner,
        created_at=j.created_at,
    )


def _to_execution_response(ex: cron_hub.JobExecution) -> ExecutionResponse:
    return ExecutionResponse(
        id=ex.id,
        job_id=ex.job_id,
        version=ex.version,
        execution_type=ex.execution_type.value,
        scheduled_at=ex.scheduled_at,
        started_at=ex.started_at,
        ended_at=ex.ended_at,
        duration_ms=ex.duration_ms,
        status=ex.status.value,
        output_summary=ex.output_summary,
        error_message=ex.error_message,
        error_type=ex.error_type.value if ex.error_type else None,
        retry_count=ex.retry_count,
        trace_id=ex.trace_id,
        triggered_by=ex.triggered_by,
    )


def _to_dlq_response(d: cron_hub.DeadLetterJob) -> DLQResponse:
    return DLQResponse(
        id=d.id,
        job_id=d.job_id,
        execution_id=d.execution_id,
        failed_at=d.failed_at,
        error_message=d.error_message,
        error_type=d.error_type.value,
        retry_exhausted=d.retry_exhausted,
        status=d.status.value,
        reviewed_by=d.reviewed_by,
        reviewed_at=d.reviewed_at,
    )


# ─── Jobs ───

@router.post("/jobs", status_code=201, response_model=JobResponse)
def create_job(req: CreateJobRequest):
    try:
        j = cron_hub.create_job(
            name=req.name,
            target_type=req.target_type,
            target_id=req.target_id,
            schedule=req.schedule,
            description=req.description,
            job_type=req.job_type,
            source_template=req.source_template,
            target_params=req.target_params,
            timezone=req.timezone,
            concurrency_policy=req.concurrency_policy,
            retry_policy=req.retry_policy,
            timeout_seconds=req.timeout_seconds,
            dry_run_supported=req.dry_run_supported,
            owner=req.owner,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return _to_job_response(j)


@router.get("/jobs", response_model=List[JobResponse])
def list_jobs(
    status: Optional[str] = None,
    job_type: Optional[str] = None,
):
    return [_to_job_response(j) for j in cron_hub.list_jobs(status, job_type)]


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str):
    j = cron_hub.get_job(job_id)
    if not j:
        raise HTTPException(status_code=404, detail="Job not found")
    return _to_job_response(j)


@router.patch("/jobs/{job_id}", response_model=JobResponse)
def update_job(job_id: str, req: UpdateJobRequest):
    j = cron_hub.get_job(job_id)
    if not j:
        raise HTTPException(status_code=404, detail="Job not found")
    data = req.model_dump(exclude_unset=True)
    updated = cron_hub.update_job(job_id, **data)
    return _to_job_response(updated)


@router.delete("/jobs/{job_id}", status_code=204)
def delete_job(job_id: str):
    ok = cron_hub.delete_job(job_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Job not found")
    return None


@router.post("/jobs/{job_id}/execute", response_model=ExecutionResponse)
def execute_job(job_id: str, req: ExecuteRequest):
    j = cron_hub.get_job(job_id)
    if not j:
        raise HTTPException(status_code=404, detail="Job not found")
    ex = cron_hub.execute_job(job_id, req.execution_type, req.triggered_by)
    return _to_execution_response(ex)


@router.post("/jobs/{job_id}/dry-run", response_model=ExecutionResponse)
def dry_run_job(job_id: str, req: ExecuteRequest):
    j = cron_hub.get_job(job_id)
    if not j:
        raise HTTPException(status_code=404, detail="Job not found")
    if not j.dry_run_supported:
        raise HTTPException(status_code=400, detail="Job does not support dry run")
    ex = cron_hub.execute_job(job_id, "DRY_RUN", req.triggered_by)
    return _to_execution_response(ex)


# ─── Executions ───

@router.get("/executions", response_model=List[ExecutionResponse])
def list_executions(
    job_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
):
    return [_to_execution_response(e) for e in cron_hub.list_executions(job_id, status, limit)]


@router.post("/executions/{execution_id}/complete", response_model=ExecutionResponse)
def complete_execution(execution_id: str, req: CompleteExecutionRequest):
    ex = cron_hub.complete_execution(
        execution_id,
        req.status,
        req.output_summary,
        req.error_message,
        req.error_type,
    )
    if not ex:
        raise HTTPException(status_code=404, detail="Execution not found")
    return _to_execution_response(ex)


@router.post("/executions/{execution_id}/retry", response_model=ExecutionResponse)
def retry_execution(execution_id: str):
    ex = cron_hub.retry_execution(execution_id)
    if not ex:
        raise HTTPException(status_code=409, detail="Retry not possible (exhausted or not found)")
    return _to_execution_response(ex)


# ─── DLQ ───

@router.get("/dlq", response_model=List[DLQResponse])
def list_dlq(
    job_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
):
    return [_to_dlq_response(d) for d in cron_hub.list_dlq(job_id, status, limit)]


@router.post("/dlq/{dlq_id}/review", response_model=DLQResponse)
def review_dlq(dlq_id: str, req: ReviewDLQRequest):
    d = cron_hub.review_dlq(dlq_id, req.decision, req.reviewed_by)
    if not d:
        raise HTTPException(status_code=404, detail="DLQ entry not found")
    return _to_dlq_response(d)


@router.post("/dlq/{dlq_id}/retry", response_model=DLQResponse)
def retry_dlq(dlq_id: str):
    d = cron_hub.retry_dlq(dlq_id)
    if not d:
        raise HTTPException(status_code=404, detail="DLQ entry not found or retry failed")
    return _to_dlq_response(d)


@router.delete("/dlq/{dlq_id}", status_code=204)
def delete_dlq(dlq_id: str):
    ok = cron_hub.delete_dlq(dlq_id)
    if not ok:
        raise HTTPException(status_code=404, detail="DLQ entry not found")


# ─── Cron Validation ───

@router.post("/validate-cron", response_model=ValidateCronResponse)
def validate_cron(req: ValidateCronRequest):
    valid = cron_hub.validate_cron(req.expression)
    nxt = None
    if valid:
        nxt = cron_hub.get_next_run(req.expression)
    return ValidateCronResponse(valid=valid, next_run=nxt)
