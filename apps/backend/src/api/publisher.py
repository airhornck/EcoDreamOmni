"""Publisher API routes: task CRUD, scheduling, execution."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_user
from src.core.database import get_db
from src.core.rbac import can_modify_publish_task, is_admin
from src.models.user import User
from src.services.publisher_service import (
    create_publish_task,
    execute_publish,
    get_publish_task,
    list_publish_tasks,
    remove_publish_task,
    update_publish_task,
)
from src.core.config import settings
from src.services import task_hub as task_hub_service
from src.services.xhs_publisher import check_account_status as check_xhs_account

router = APIRouter(prefix="/publish-tasks", tags=["publisher"])
platform_router = APIRouter(prefix="/platforms", tags=["publisher"])


# ─── Request/Response Models ───


class CreatePublishTaskRequest(BaseModel):
    draft_id: str
    account_id: str
    platform: str = Field(..., description="xhs, douyin, wechat_channels")
    scheduled_at: Optional[str] = None
    task_hub_task_id: Optional[str] = None


class UpdatePublishTaskRequest(BaseModel):
    status: Optional[str] = None
    scheduled_at: Optional[str] = None


class PublishTaskResponse(BaseModel):
    id: str
    draft_id: str
    account_id: str
    platform: str
    status: str
    scheduled_at: Optional[str] = None
    published_at: Optional[str] = None
    published_url: Optional[str] = None
    platform_post_id: Optional[str] = None
    error_reason: Optional[str] = None
    publish_skipped_reason: Optional[str] = None
    retry_count: int
    created_at: str
    updated_at: str


class PublishTaskListResponse(BaseModel):
    tasks: List[PublishTaskResponse]
    total: int


class ExecutePublishRequest(BaseModel):
    content: dict = Field(default_factory=dict, description="{title, body, tags}")
    format_name: Optional[str] = Field(None, description="内容格式名称，如: 图文, 视频, 仅文字。不传则自动推断。")


class ExecutePublishResponse(BaseModel):
    task_id: str
    success: bool
    status: str
    published_url: Optional[str] = None
    error_reason: Optional[str] = None


class XhsAccountStatusResponse(BaseModel):
    healthy: bool
    reason: str
    user_id: str
    nickname: str


# ─── Helpers ───


def _to_response(task) -> PublishTaskResponse:
    return PublishTaskResponse(
        id=task.id,
        draft_id=task.draft_id,
        account_id=task.account_id,
        platform=task.platform,
        status=task.status,
        scheduled_at=task.scheduled_at,
        published_at=task.published_at,
        published_url=task.published_url,
        platform_post_id=task.platform_post_id,
        error_reason=task.error_reason,
        publish_skipped_reason=task.publish_skipped_reason,
        retry_count=task.retry_count,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


# ─── Routes ───


@router.post("", status_code=status.HTTP_201_CREATED, response_model=PublishTaskResponse)
async def create_task(
    req: CreatePublishTaskRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Unified publish entry: require task_hub_task_id and APPROVED_WAITING_PUBLISH status
    if not req.task_hub_task_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Publish task creation must go through review-publish-center confirm-publish. "
                   "Provide task_hub_task_id or use POST /review-publish-center/conclusions/{id}/confirm-publish",
        )

    t = await task_hub_service.get_task(db, req.task_hub_task_id)
    if not t:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"TaskHub task {req.task_hub_task_id} not found",
        )
    if t.status != task_hub_service.TaskStatus.APPROVED_WAITING_PUBLISH:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"TaskHub task is not in APPROVED_WAITING_PUBLISH status (current: {t.status.value})",
        )

    task = await create_publish_task(
        draft_id=req.draft_id,
        account_id=req.account_id,
        platform=req.platform,
        scheduled_at=req.scheduled_at,
        task_hub_task_id=req.task_hub_task_id,
        created_by=user.id,
    )

    # Sync task_hub task status to running (same as confirm-publish)
    await task_hub_service.transition_task(db, req.task_hub_task_id, "running")

    return _to_response(task)


@router.get("", response_model=PublishTaskListResponse)
def list_tasks(user: User = Depends(get_current_user)):
    created_by = None if is_admin(user) else user.id
    tasks = list_publish_tasks(created_by=created_by)
    return PublishTaskListResponse(tasks=[_to_response(t) for t in tasks], total=len(tasks))


@router.get("/{task_id}", response_model=PublishTaskResponse)
def get_task(task_id: str, user: User = Depends(get_current_user)):
    task = get_publish_task(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.created_by and task.created_by != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: not the task owner")
    return _to_response(task)


@router.patch("/{task_id}", response_model=PublishTaskResponse)
def update_task(task_id: str, req: UpdatePublishTaskRequest, user: User = Depends(get_current_user)):
    task = get_publish_task(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.created_by and task.created_by != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: not the task owner")
    kwargs = req.model_dump(exclude_unset=True)
    task = update_publish_task(task_id, **kwargs)
    return _to_response(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str, user: User = Depends(get_current_user)):
    task = get_publish_task(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if not can_modify_publish_task(user, task):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: not the task owner")
    removed = remove_publish_task(task_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return None


@router.post("/{task_id}/execute", response_model=ExecutePublishResponse)
def execute_task(task_id: str, req: ExecutePublishRequest, user: User = Depends(get_current_user)):
    task = get_publish_task(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if not can_modify_publish_task(user, task):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: not the task owner")

    try:
        updated = execute_publish(task_id, req.content, format_name=req.format_name)
        return ExecutePublishResponse(
            task_id=task_id,
            success=updated.status == "published",
            status=updated.status,
            published_url=updated.published_url,
            error_reason=updated.error_reason,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


class XhsHealthCheckRequest(BaseModel):
    account_id: Optional[str] = None


@platform_router.post("/xiaohongshu/health-check", response_model=XhsAccountStatusResponse)
def xhs_health_check(req: XhsHealthCheckRequest, user: User = Depends(get_current_user)):
    """Check whether the configured XHS account is healthy and can publish.

    If account_id is provided, checks that specific account's cookie.
    Otherwise checks the global REDNOTE_COOKIE.
    """
    from src.models.account_pool import get_pool_entry

    if req.account_id:
        account = get_pool_entry(req.account_id)
        if account is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
        cookie = account.cookie
    else:
        cookie = settings.REDNOTE_COOKIE

    status = check_xhs_account(cookie)
    return XhsAccountStatusResponse(
        healthy=status["healthy"],
        reason=status["reason"],
        user_id=status["user_id"],
        nickname=status["nickname"],
    )


@platform_router.get("/xhs/account-status", response_model=XhsAccountStatusResponse)
def xhs_account_status(account_id: Optional[str] = None, user: User = Depends(get_current_user)):
    """Check whether the configured XHS account is healthy and can publish.

    If account_id is provided, checks that specific account's cookie.
    Otherwise checks the global REDNOTE_COOKIE.
    """
    from src.models.account_pool import get_pool_entry

    if account_id:
        account = get_pool_entry(account_id)
        if account is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
        cookie = account.cookie
    else:
        cookie = settings.REDNOTE_COOKIE

    status = check_xhs_account(cookie)
    return XhsAccountStatusResponse(
        healthy=status["healthy"],
        reason=status["reason"],
        user_id=status["user_id"],
        nickname=status["nickname"],
    )
