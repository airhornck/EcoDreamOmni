"""Human-in-the-Loop API — Phase 2 / PRD V2.6 §10.6.

Routes:
  GET  /human-in-loop/pending              # Pending review tasks
  GET  /human-in-loop/tasks/{id}           # Review detail
  POST /human-in-loop/tasks/{id}/approve   # Approve
  POST /human-in-loop/tasks/{id}/reject    # Reject
  POST /human-in-loop/tasks/{id}/revise    # Revise
  GET  /human-in-loop/history              # Review history
  GET  /human-in-loop/stats                # Review stats
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.dependencies import get_current_user
from src.core.rbac import can_review_task, can_view_task, is_admin
from src.models.user import User
from src.services import human_in_loop
from src.services import task_hub

router = APIRouter(prefix="/human-in-the-loop", tags=["human-in-the-loop"])


# ─── Schemas ───

class ApproveRequest(BaseModel):
    operator: Optional[str] = None
    publish_mode: Optional[str] = None
    scheduled_at: Optional[str] = None
    cron_schedule: Optional[str] = None
    copilot_suggested: bool = False
    copilot_card_id: Optional[str] = None


class RejectRequest(BaseModel):
    operator: Optional[str] = None
    reason: str
    copilot_suggested: bool = False
    copilot_card_id: Optional[str] = None


class ReviseRequest(BaseModel):
    operator: Optional[str] = None
    target_node_index: int = 3
    revised_variables: Dict[str, Any] = {}
    reason: str = ""


class PendingTaskResponse(BaseModel):
    task_id: str
    task_name: str
    status: str
    content_preview: str
    agent_summary: str
    prompt_variables: Dict[str, Any]
    priority: int
    waiting_since: str
    requires_dual_approval: bool


class ReviewDetailResponse(BaseModel):
    task_id: str
    task_name: str
    status: str
    content_preview: str
    agent_summary: str
    prompt_variables: Dict[str, Any]
    workflow_template_id: str
    current_node_index: int
    waiting_since: str
    requires_dual_approval: bool
    has_primary_approval: bool
    review_history: List[Dict[str, Any]]


class ReviewActionResponse(BaseModel):
    task_id: str
    status: str
    reviewer: Optional[str] = None
    message: Optional[str] = None
    copilot_followup: Optional[Dict[str, Any]] = None


class ReviewHistoryItem(BaseModel):
    reviewer: str
    decision: str
    reason: Optional[str]
    created_at: str


class StatsResponse(BaseModel):
    total_reviews: int
    approved: int
    rejected: int
    revised: int
    pending: int


# ─── W17: Risk Detection ───

class DetectRiskRequest(BaseModel):
    title: str = ""
    body: str = ""
    tags: List[str] = []


class DetectRiskResponse(BaseModel):
    risk_level: str
    reasons: List[str]
    review_strategy: str
    requires_forced_individual_review: bool


class MarkRiskRequest(BaseModel):
    risk_level: str
    reason: str = ""


class MarkRiskResponse(BaseModel):
    task_id: str
    risk_level: str
    review_strategy: str
    reason: str


class BatchApproveRequest(BaseModel):
    task_ids: List[str]
    reviewer_id: str


class BatchApproveResponse(BaseModel):
    approved_count: int
    rejected_count: int
    forced_individual_review_count: int
    forced_individual_review_ids: List[str]


# ─── Pending Reviews ───

@router.get("/pending")
async def get_pending_tasks(
    reviewer_role: Optional[str] = None,
    account_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    created_by = None if is_admin(user) or user.role == "reviewer" else user.id
    items = [
        {
            "task_id": p.task_id,
            "task_name": p.task_name,
            "status": p.status,
            "content_preview": p.content_preview,
            "agent_summary": p.agent_summary,
            "prompt_variables": p.prompt_variables,
            "priority": p.priority,
            "waiting_since": p.waiting_since,
            "requires_dual_approval": p.requires_dual_approval,
            "risk_level": p.risk_level.value,
            "review_strategy": p.review_strategy.value,
        }
        for p in await human_in_loop.get_pending_tasks(db, reviewer_role, account_id, created_by=created_by)
    ]
    return {"items": items, "total": len(items)}


@router.get("/tasks/{task_id}", response_model=ReviewDetailResponse)
async def get_review_detail(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = await task_hub.get_task(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    if not can_view_task(user, t):
        raise HTTPException(status_code=403, detail="Forbidden: not authorized to view this task")
    detail = await human_in_loop.get_review_detail(db, task_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Task not found")
    return ReviewDetailResponse(
        task_id=detail["task_id"],
        task_name=detail["task_name"],
        status=detail["status"],
        content_preview=detail["content_preview"],
        agent_summary=detail["agent_summary"],
        prompt_variables=detail["prompt_variables"],
        workflow_template_id=detail["workflow_template_id"],
        current_node_index=detail["current_node_index"],
        waiting_since=detail["waiting_since"],
        requires_dual_approval=detail["requires_dual_approval"],
        has_primary_approval=detail["has_primary_approval"],
        review_history=detail["review_history"],
    )


# ─── Review Actions ───

@router.post("/tasks/{task_id}/approve", response_model=ReviewActionResponse)
async def approve_task(
    task_id: str,
    req: ApproveRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = await task_hub.get_task(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    if not can_review_task(user, t):
        raise HTTPException(status_code=403, detail="Forbidden: not authorized to review this task")
    try:
        result = await human_in_loop.approve_task(
            db, task_id, user.id, req.publish_mode, req.scheduled_at
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    # Build copilot_followup for approve → publish confirmation
    copilot_followup = None
    if result.get("status") == "approved_waiting_publish":
        copilot_followup = {
            "message": "审核已通过！要现在发布还是定时发布？",
            "suggested_cards": [
                {
                    "type": "decision",
                    "title": "发布确认",
                    "actions": [
                        {"id": "publish_now", "label": "立即发布", "variant": "primary"},
                        {"id": "schedule", "label": "定时发布", "variant": "secondary"},
                    ],
                }
            ],
        }

    return ReviewActionResponse(
        task_id=result["task_id"],
        status=result["status"],
        reviewer=user.id,
        message=result.get("message"),
        copilot_followup=copilot_followup,
    )


@router.post("/tasks/{task_id}/reject", response_model=ReviewActionResponse)
async def reject_task(
    task_id: str,
    req: RejectRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = await task_hub.get_task(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    if not can_review_task(user, t):
        raise HTTPException(status_code=403, detail="Forbidden: not authorized to review this task")
    try:
        result = await human_in_loop.reject_task(db, task_id, user.id, req.reason)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    # Build copilot_followup for reject
    copilot_followup = {
        "message": "内容已驳回。可以在内容生产页面查看详情并重新生成。",
        "suggested_cards": [
            {
                "type": "suggestion",
                "title": "重新生成",
                "actions": [
                    {"id": "regenerate", "label": "重新生成内容", "variant": "primary"},
                ],
            }
        ],
    }

    return ReviewActionResponse(
        task_id=result["task_id"],
        status=result["status"],
        reviewer=user.id,
        copilot_followup=copilot_followup,
    )


@router.post("/tasks/{task_id}/revise", response_model=ReviewActionResponse)
async def revise_task(
    task_id: str,
    req: ReviseRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = await task_hub.get_task(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    if not can_review_task(user, t):
        raise HTTPException(status_code=403, detail="Forbidden: not authorized to review this task")
    try:
        result = await human_in_loop.revise_task(
            db, task_id, user.id, req.target_node_index, req.revised_variables, req.reason
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    # Build copilot_followup for revise
    copilot_followup = {
        "message": "内容已打回修改。请前往内容生产页面根据反馈进行调整。",
        "suggested_cards": [
            {
                "type": "suggestion",
                "title": "前往编辑",
                "actions": [
                    {"id": "goto_edit", "label": "去编辑", "variant": "primary"},
                ],
            }
        ],
    }

    return ReviewActionResponse(
        task_id=result["task_id"],
        status=result["status"],
        reviewer=user.id,
        copilot_followup=copilot_followup,
    )


# ─── History & Stats ───

@router.get("/history", response_model=List[ReviewHistoryItem])
def get_history(
    reviewer: Optional[str] = None,
    decision: Optional[str] = None,
    limit: int = 100,
):
    return [
        ReviewHistoryItem(
            reviewer=r.reviewer,
            decision=r.decision,
            reason=r.reason,
            created_at=r.created_at,
        )
        for r in human_in_loop.get_all_reviews(reviewer, decision, limit)
    ]


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    db: AsyncSession = Depends(get_db),
):
    stats = await human_in_loop.get_review_stats(db)
    return StatsResponse(
        total_reviews=stats["total_reviews"],
        approved=stats["approved"],
        rejected=stats["rejected"],
        revised=stats["revised"],
        pending=stats["pending"],
    )


# ─── W17 Routes ───

@router.post("/detect-risk", response_model=DetectRiskResponse)
def detect_risk(req: DetectRiskRequest):
    result = human_in_loop.detect_content_risk(req.title, req.body, req.tags)
    return DetectRiskResponse(**result)


@router.post("/tasks/{task_id}/mark-risk", response_model=MarkRiskResponse)
async def mark_task_risk(
    task_id: str,
    req: MarkRiskRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = await task_hub.get_task(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    if t.created_by != user.id:
        raise HTTPException(status_code=403, detail="Forbidden: not the task owner")
    result = await human_in_loop.mark_task_risk(db, task_id, req.risk_level, req.reason)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return MarkRiskResponse(**result)


@router.post("/batch-approve", response_model=BatchApproveResponse)
async def batch_approve(
    req: BatchApproveRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Filter out tasks not owned by current user
    owned_task_ids = []
    for tid in req.task_ids:
        t = await task_hub.get_task(db, tid)
        if t and t.created_by == user.id:
            owned_task_ids.append(tid)
    result = await human_in_loop.batch_approve(db, owned_task_ids, user.id)
    return BatchApproveResponse(**result)
