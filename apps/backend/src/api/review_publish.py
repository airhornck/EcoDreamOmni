"""Review Publish Center API — v2 transformation.

Routes:
  GET  /review-publish-center/conclusions          # Aggregated review conclusions list
  GET  /review-publish-center/conclusions/{id}     # Review conclusion detail
  POST /review-publish-center/conclusions/{id}/confirm-publish  # Confirm publish (immediate/scheduled/cron)
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.core.dependencies import get_current_user
from src.core.rbac import can_modify_task, can_view_task, is_admin
from src.models.user import User
from pydantic import BaseModel

from src.services import human_in_loop, task_hub
from src.services.account_pool_service import get_account
from src.services.cron_hub import create_job
from src.services.publisher_service import create_publish_task

router = APIRouter(prefix="/review-publish-center", tags=["review-publish-center"])


# ─── Schemas ───

class ConfirmPublishRequest(BaseModel):
    operator: Optional[str] = None
    publish_mode: str = "immediate"  # immediate / scheduled
    scheduled_at: Optional[str] = None
    cron_schedule: Optional[str] = None  # e.g. "0 9 * * *"
    cron_date_start: Optional[str] = None  # YYYY-MM-DD
    cron_date_end: Optional[str] = None    # YYYY-MM-DD


class ReviewConclusionItem(BaseModel):
    task_id: str
    task_name: str
    content_title: Optional[str] = None
    platform: str
    account_name: str
    status: str
    review_decision: Optional[str]
    reviewed_at: Optional[str]
    reviewer: Optional[str]
    review_reason: Optional[str]
    content_preview: str
    waiting_since: str
    priority: int
    risk_level: str
    can_publish_now: bool
    has_cron_job: bool


class ReviewConclusionListResponse(BaseModel):
    items: List[ReviewConclusionItem]
    total: int
    copilot_summary: Optional[Dict[str, Any]] = None


class ReviewDetailResponse(BaseModel):
    task_id: str
    task_name: str
    platform: str
    status: str
    content_preview: str
    generated_content: Optional[Dict[str, Any]] = None
    agent_summary: str
    compliance_result: Dict[str, Any]
    prediction_result: Dict[str, Any]
    quality_score: Dict[str, Any]
    injection_context: Dict[str, Any]
    topic_report: Optional[Dict[str, Any]] = None
    cover_image_url: Optional[str]
    review_history: List[Dict[str, Any]]
    risk_level: str
    can_publish: bool
    has_primary_approval: bool = False
    account_id: str
    account_name: str
    draft_id: Optional[str]
    cron_schedule: Optional[str] = None
    copilot_context: Optional[Dict[str, Any]] = None
    available_copilot_cards: Optional[List[str]] = None


class ConfirmPublishResponse(BaseModel):
    task_id: str
    status: str
    publish_mode: str
    scheduled_at: Optional[str]
    cron_job_id: Optional[str]
    publish_task_id: Optional[str]


class UpdateContentRequest(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    tags: Optional[List[str]] = None
    cover_image_url: Optional[str] = None


class UpdateContentResponse(BaseModel):
    success: bool
    updated_at: str


class RegenerateContentResponse(BaseModel):
    success: bool
    status: str
    message: str


# ─── Helpers ───

def _get_account_name(account_id: str) -> str:
    acct = get_account(account_id)
    if acct:
        return getattr(acct, "nickname", None) or getattr(acct, "username", None) or account_id
    return account_id


def _get_draft_id(prompt_variables: Dict[str, Any]) -> Optional[str]:
    return prompt_variables.get("draft_id") or prompt_variables.get("draftId")


# ─── Review Conclusions List ───

@router.get("/conclusions", response_model=ReviewConclusionListResponse)
async def get_review_conclusions(
    status_filter: Optional[str] = None,
    platform: Optional[str] = None,
    account_id: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Aggregate review conclusions for the review-publish center."""
    created_by = None if is_admin(user) else user.id
    all_tasks = await task_hub.list_tasks(db, created_by=created_by)

    results = []
    for t in all_tasks:
        # Include tasks with review decisions or currently in HUMAN_WAIT
        if not (t.review_decision or t.status in {
            task_hub.TaskStatus.HUMAN_WAIT,
            task_hub.TaskStatus.APPROVED_WAITING_PUBLISH,
        }):
            continue

        # Filter by platform
        if platform and t.platform != platform:
            continue
        if account_id and t.account_id != account_id:
            continue

        # Filter by status if requested
        if status_filter:
            if status_filter == "approved" and t.review_decision != "APPROVE":
                continue
            if status_filter == "rejected" and t.review_decision != "REJECT":
                continue
            if status_filter == "revised" and t.review_decision != "REVISE":
                continue
            if status_filter == "pending" and t.status != task_hub.TaskStatus.HUMAN_WAIT:
                continue

        risk_info = human_in_loop.get_task_risk(t.id)
        # Note: human_in_loop is still sync/in-memory; acceptable for MVP
        preview = t.prompt_variables.get("content_preview", "")
        gc = t.prompt_variables.get("generated_content", {})
        content_title = gc.get("title") if isinstance(gc, dict) else None

        results.append(
            ReviewConclusionItem(
                task_id=t.id,
                task_name=t.name,
                content_title=content_title,
                platform=t.platform,
                account_name=_get_account_name(t.account_id),
                status=t.status.value,
                review_decision=t.review_decision,
                reviewed_at=t.reviewed_at,
                reviewer=t.reviewer,
                review_reason=t.review_reason,
                content_preview=preview[:200] if isinstance(preview, str) else "",
                waiting_since=t.updated_at,
                priority=t.priority,
                risk_level=risk_info.get("risk_level", "LOW"),
                can_publish_now=t.status == task_hub.TaskStatus.APPROVED_WAITING_PUBLISH,
                has_cron_job=t.cron_job_id is not None,
            )
        )

    # Sort: APPROVED_WAITING_PUBLISH first → by priority desc → by time asc
    results.sort(key=lambda x: (
        0 if x.status == "approved_waiting_publish" else 1,
        0 if x.status == "human_wait" else 1,
        -x.priority,
        x.waiting_since,
    ))

    # Build copilot summary for list view
    pending = [r for r in results if r.status == "human_wait"]
    copilot_summary = {
        "total_pending": len(pending),
        "recommended_priority": sorted(
            [p.task_id for p in pending],
            key=lambda tid: next((x.priority for x in pending if x.task_id == tid), 0),
            reverse=True,
        ),
        "batch_suggestion": f"{len(pending)} 条待审中，建议按优先级从高到低处理。",
    } if pending else None

    return ReviewConclusionListResponse(
        items=results[:limit],
        total=len(results),
        copilot_summary=copilot_summary,
    )


# ─── Review Conclusion Detail ───

@router.get("/conclusions/{task_id}", response_model=ReviewDetailResponse)
async def get_review_conclusion_detail(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get full detail for a review conclusion (content preview + agent summary + review history)."""
    t = await task_hub.get_task(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    if not can_view_task(user, t):
        raise HTTPException(status_code=403, detail="Forbidden: not authorized to view this task")

    history = await human_in_loop.get_review_history(db, task_id)
    risk_info = human_in_loop.get_task_risk(task_id)

    # Fallback generated_content if missing (e.g. task created without workflow content)
    gc = t.prompt_variables.get("generated_content")
    preview = t.prompt_variables.get("content_preview", "")
    if not gc and preview:
        gc = {
            "title": t.name,
            "body": preview,
            "tags": [],
            "platform": t.platform,
            "content_type": "note",
            "content_format": t.content_format or "图文",
            "cover_image_url": t.prompt_variables.get("cover_image_url", ""),
        }

    # Build copilot context for detail view
    compliance = t.prompt_variables.get("compliance_result", {})
    quality = t.prompt_variables.get("quality_score", {})
    comp_score = compliance.get("score") or compliance.get("overall", 80)
    qual_score = quality.get("overall", 80) if isinstance(quality, dict) else 80
    copilot_context = {
        "recommended_action": "approve" if comp_score >= 85 else "revise",
        "confidence": 0.94 if comp_score >= 85 else 0.65,
        "reasoning": f"合规分 {comp_score} 分，L1-L4 {'全部通过' if comp_score >= 80 else '部分未通过'}，质量分 {qual_score} 分",
        "risk_factors": [] if comp_score >= 80 else ["合规分偏低"],
        "suggested_improvements": [
            "标题加入具体数字可提升点击率",
            "文末添加驱虫时间表卡片",
        ] if comp_score >= 90 else [
            "补充图片来源标注",
            "调整标题关键词密度",
        ],
    }

    return ReviewDetailResponse(
        task_id=t.id,
        task_name=t.name,
        platform=t.platform,
        status=t.status.value,
        content_preview=preview,
        generated_content=gc,
        agent_summary=t.prompt_variables.get("agent_summary", ""),
        compliance_result=compliance,
        prediction_result=t.prompt_variables.get("prediction_result", {}),
        quality_score=quality,
        injection_context=t.prompt_variables.get("injection_context", {}),
        topic_report=t.prompt_variables.get("topic_report"),
        cover_image_url=t.prompt_variables.get("cover_image_url"),
        review_history=[
            {
                "reviewer": r.reviewer,
                "decision": r.decision,
                "reason": r.reason,
                "publish_mode": r.publish_mode,
                "scheduled_at": r.scheduled_at,
                "created_at": r.created_at,
            }
            for r in history
        ],
        risk_level=risk_info.get("risk_level", "LOW"),
        can_publish=t.status == task_hub.TaskStatus.APPROVED_WAITING_PUBLISH,
        has_primary_approval=any(r.decision == "APPROVE" for r in history),
        account_id=t.account_id,
        account_name=_get_account_name(t.account_id),
        draft_id=_get_draft_id(t.prompt_variables),
        cron_schedule=t.prompt_variables.get("cron_schedule"),
        copilot_context=copilot_context,
        available_copilot_cards=["review-decision", "cover-generation", "title-optimization"],
    )


# ─── Confirm Publish ───

@router.post("/conclusions/{task_id}/confirm-publish", response_model=ConfirmPublishResponse)
async def confirm_publish(
    task_id: str,
    req: ConfirmPublishRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Confirm publish from the review-publish center (immediate / scheduled / cron)."""
    t = await task_hub.get_task(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    if not can_modify_task(user, t):
        raise HTTPException(status_code=403, detail="Forbidden: not authorized to publish this task")
    if t.status != task_hub.TaskStatus.APPROVED_WAITING_PUBLISH:
        raise HTTPException(
            status_code=409,
            detail=f"Task is not in APPROVED_WAITING_PUBLISH status (current: {t.status.value})",
        )

    draft_id = _get_draft_id(t.prompt_variables)
    if not draft_id:
        raise HTTPException(status_code=422, detail="Task has no associated draft_id")

    # 1. Create publish task
    try:
        publish_task = await create_publish_task(
            draft_id=draft_id,
            account_id=t.account_id,
            platform=t.platform,
            scheduled_at=req.scheduled_at if req.publish_mode == "scheduled" else None,
            task_hub_task_id=task_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create publish task: {e}")

    # 2. Create CronJob if loop requested
    cron_job_id = None
    if req.cron_schedule:
        try:
            job = create_job(
                name=f"循环发布: {t.name}",
                target_type="API",
                target_id="publish-task",
                schedule=req.cron_schedule,
                description=f"Recurring publish for task {task_id}",
                target_params={
                    "draft_id": draft_id,
                    "account_id": t.account_id,
                    "platform": t.platform,
                    "date_range_start": req.cron_date_start,
                    "date_range_end": req.cron_date_end,
                },
                concurrency_policy="SKIP",
                owner=req.operator,
            )
            cron_job_id = job.id
        except ValueError as e:
            raise HTTPException(status_code=422, detail=f"Invalid cron schedule: {e}")

    # 3. Update task status to RUNNING and record publish confirmation
    await task_hub.transition_task(db, task_id, "running")
    await task_hub.update_task(
        db,
        task_id,
        publish_confirmed_at=task_hub._now(),
        publish_confirmer=user.id,
        cron_job_id=cron_job_id,
    )

    # 4. Resume workflow execution to drive the publisher node
    t = await task_hub.get_task(db, task_id)
    if t and t.execution_id:
        await task_hub.resume_workflow_execution(db, t)

    return ConfirmPublishResponse(
        task_id=task_id,
        status="running",
        publish_mode=req.publish_mode,
        scheduled_at=req.scheduled_at,
        cron_job_id=cron_job_id,
        publish_task_id=publish_task.id,
    )


# ─── Update Review Content ───

@router.put("/conclusions/{task_id}/content", response_model=UpdateContentResponse)
async def update_review_content(
    task_id: str,
    req: UpdateContentRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update review content (title/body/tags/cover) and record modification metadata."""
    t = await task_hub.get_task(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    if not can_modify_task(user, t):
        raise HTTPException(status_code=403, detail="Forbidden: not authorized to modify this task")

    # Merge updates into prompt_variables.generated_content
    pv = dict(t.prompt_variables)
    generated = dict(pv.get("generated_content") or {})
    if req.title is not None:
        generated["title"] = req.title
    if req.body is not None:
        generated["body"] = req.body
        pv["content_preview"] = req.body[:200]
    if req.tags is not None:
        generated["tags"] = req.tags
    if req.cover_image_url is not None:
        generated["cover_image_url"] = req.cover_image_url
        pv["cover_image_url"] = req.cover_image_url

    pv["generated_content"] = generated
    pv["content_modified_at"] = datetime.now(timezone.utc).isoformat()
    pv["content_modified_by"] = user.id

    # Mark compliance as stale since content changed
    pv["compliance_result"] = {
        **(pv.get("compliance_result") or {}),
        "level": "stale",
        "note": "内容已修改，建议重新审核",
    }

    # Use update_task to persist prompt_variables to DB
    await task_hub.update_task(db, task_id, prompt_variables=pv)
    return UpdateContentResponse(success=True, updated_at=datetime.now(timezone.utc).isoformat())


# ─── Regenerate Content ───

@router.post("/conclusions/{task_id}/regenerate", response_model=RegenerateContentResponse)
async def regenerate_content(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Re-run the full workflow for the task to regenerate content end-to-end.

    1. Delete old workflow execution
    2. Reset task to DRAFT
    3. Call start_workflow to drive: 选题→结构→框架→正文(LLM)→合规→预演→人工审核
    """
    t = await task_hub.get_task(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    if not can_modify_task(user, t):
        raise HTTPException(status_code=403, detail="Forbidden: not authorized to regenerate this task")

    from src.services import workflow_engine as we

    # 1. Clear old execution and reset task for re-run
    if t.execution_id:
        we.delete_execution(t.execution_id)
    await task_hub.update_task(db, task_id, execution_id=None, current_node_index=0, review_decision=None, reviewer=None, reviewed_at=None, review_reason=None)

    # 2. Start workflow — start_workflow internally transitions through CONFIGURING → QUEUED → RUNNING
    #    HUMAN_WAIT → CONFIGURING is a valid state-machine transition.
    task = await task_hub.start_workflow(db, task_id)
    if not task:
        raise HTTPException(status_code=500, detail="工作流启动失败")

    # 3. Record regeneration metadata
    pv = dict(task.prompt_variables)
    pv["regenerate_requested_at"] = datetime.now(timezone.utc).isoformat()
    pv["regenerate_requested_by"] = user.id
    pv["regenerate_count"] = pv.get("regenerate_count", 0) + 1
    await task_hub.update_task(db, task_id, prompt_variables=pv)

    return RegenerateContentResponse(
        success=True,
        status=task.status.value,
        message="工作流已重新执行，内容已生成",
    )
