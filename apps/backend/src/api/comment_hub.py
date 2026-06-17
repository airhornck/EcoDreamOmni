"""CommentHub API — W16 合规评论管理路由。

合规红线:
- 不存在自动发布接口
- 所有回复必须经过人工审核
- 诱导话术自动拦截
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.api.auth import get_current_user
from src.services.comment_hub import (
    approve_reply,
    get_account_stats,
    list_pending_replies,
    reject_reply,
    submit_reply,
    suggest_reply,
)

router = APIRouter(prefix="/comments", tags=["comment-hub"])


# ─── Request/Response Models ───


class SuggestReplyRequest(BaseModel):
    account_id: str
    original_comment: str


class SuggestReplyResponse(BaseModel):
    reply_id: str
    suggested_reply: str
    status: str
    risk_level: str
    sentiment: str
    inducement_detected: bool
    blocked_keywords: List[str]


class SubmitReplyRequest(BaseModel):
    final_reply: str


class ReviewActionRequest(BaseModel):
    reviewer_id: str


class RejectRequest(BaseModel):
    reviewer_id: str
    reason: str


class ReplyOut(BaseModel):
    id: str
    content_id: str
    account_id: str
    original_comment: str
    suggested_reply: str
    final_reply: Optional[str]
    status: str
    risk_level: str
    inducement_detected: bool
    sentiment: str
    reviewed_by: Optional[str]
    reviewed_at: Optional[str]
    reject_reason: Optional[str]


class PendingListResponse(BaseModel):
    items: List[ReplyOut]
    total: int


class AccountStatsResponse(BaseModel):
    account_id: str
    total_replies: int
    pending_review: int
    approved: int
    rejected: int
    daily_published_count: int
    daily_limit: int


# ─── Helpers ───


def _reply_to_out(reply) -> ReplyOut:
    return ReplyOut(
        id=reply.id,
        content_id=reply.content_id,
        account_id=reply.account_id,
        original_comment=reply.original_comment,
        suggested_reply=reply.suggested_reply,
        final_reply=reply.final_reply,
        status=reply.status,
        risk_level=reply.risk_level,
        inducement_detected=reply.inducement_detected,
        sentiment=reply.sentiment,
        reviewed_by=reply.reviewed_by,
        reviewed_at=reply.reviewed_at,
        reject_reason=reply.reject_reason,
    )


# ─── Routes ───


@router.post("/{content_id}/replies/suggest", response_model=SuggestReplyResponse)
def suggest_reply_route(
    content_id: str,
    req: SuggestReplyRequest,
    user=Depends(get_current_user),
):
    reply = suggest_reply(
        content_id=content_id,
        account_id=req.account_id,
        original_comment=req.original_comment,
    )
    return SuggestReplyResponse(
        reply_id=reply.id,
        suggested_reply=reply.suggested_reply,
        status=reply.status,
        risk_level=reply.risk_level,
        sentiment=reply.sentiment,
        inducement_detected=reply.inducement_detected,
        blocked_keywords=reply.blocked_keywords,
    )


@router.post("/replies/{reply_id}/submit", response_model=ReplyOut)
def submit_reply_route(
    reply_id: str,
    req: SubmitReplyRequest,
    user=Depends(get_current_user),
):
    reply = submit_reply(reply_id=reply_id, final_reply=req.final_reply)
    if not reply:
        raise HTTPException(status_code=404, detail="Reply not found")
    return _reply_to_out(reply)


@router.post("/replies/{reply_id}/approve", response_model=ReplyOut)
def approve_reply_route(
    reply_id: str,
    req: ReviewActionRequest,
    user=Depends(get_current_user),
):
    reply = approve_reply(reply_id=reply_id, reviewer_id=req.reviewer_id)
    if not reply:
        raise HTTPException(status_code=404, detail="Reply not found")
    return _reply_to_out(reply)


@router.post("/replies/{reply_id}/reject", response_model=ReplyOut)
def reject_reply_route(
    reply_id: str,
    req: RejectRequest,
    user=Depends(get_current_user),
):
    reply = reject_reply(
        reply_id=reply_id, reviewer_id=req.reviewer_id, reason=req.reason
    )
    if not reply:
        raise HTTPException(status_code=404, detail="Reply not found")
    return _reply_to_out(reply)


@router.get("/pending-review", response_model=PendingListResponse)
def list_pending_replies_route(user=Depends(get_current_user)):
    items = list_pending_replies()
    return PendingListResponse(items=[_reply_to_out(r) for r in items], total=len(items))


@router.get("/account/{account_id}/stats", response_model=AccountStatsResponse)
def get_account_stats_route(
    account_id: str,
    user=Depends(get_current_user),
):
    stats = get_account_stats(account_id)
    return AccountStatsResponse(**stats)
