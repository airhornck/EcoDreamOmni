"""Pipeline API — Async task submission and status monitoring."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from src.api.auth import get_current_user
from src.services import pipeline_service

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


class TaskSubmit(BaseModel):
    task_type: str  # publish, data_analysis, model_training, trend_crawl
    payload: dict = {}


class TaskOut(BaseModel):
    task_id: str
    task_type: str
    status: str
    result: Optional[dict] = None
    error_message: Optional[str] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress_percent: int

    model_config = ConfigDict(from_attributes=True)


@router.post("/tasks", status_code=201, response_model=TaskOut)
def submit_task(data: TaskSubmit, user=Depends(get_current_user)):
    task = pipeline_service.submit_task(data.task_type, data.payload)
    pipeline_service.run_task_in_background(task.task_id)
    return TaskOut(
        task_id=task.task_id,
        task_type=task.task_type,
        status=task.status,
        result=task.result,
        error_message=task.error_message,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        progress_percent=task.progress_percent,
    )


@router.get("/tasks/{task_id}", response_model=TaskOut)
def get_task_status(task_id: str, user=Depends(get_current_user)):
    task = pipeline_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskOut(
        task_id=task.task_id,
        task_type=task.task_type,
        status=task.status,
        result=task.result,
        error_message=task.error_message,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        progress_percent=task.progress_percent,
    )


@router.get("/tasks")
def list_tasks(task_type: Optional[str] = None, status: Optional[str] = None, user=Depends(get_current_user)):
    tasks = pipeline_service.list_tasks(task_type=task_type, status=status)
    return {
        "tasks": [
            TaskOut(
                task_id=t.task_id,
                task_type=t.task_type,
                status=t.status,
                result=t.result,
                error_message=t.error_message,
                created_at=t.created_at,
                started_at=t.started_at,
                completed_at=t.completed_at,
                progress_percent=t.progress_percent,
            )
            for t in tasks
        ]
    }


@router.post("/tasks/{task_id}/cancel")
def cancel_task(task_id: str, user=Depends(get_current_user)):
    if not pipeline_service.cancel_task(task_id):
        raise HTTPException(status_code=400, detail="Task cannot be cancelled (not pending or running)")
    return {"status": "cancelled"}
