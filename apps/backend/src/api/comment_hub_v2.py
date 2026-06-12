"""CommentHub v2 Extended API — v4.0 Phase 2 P2-3.

新增监控/策略/预警路由，与现有 comment_hub.py 并存。
Aligned with docs/契约与数据/01-API接口契约.md §4.3 (CommentHub 扩展)。
"""

from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.api.auth import get_current_user
from src.services.comment_hub_monitor import (
    Alert,
    AlertRule,
    CommentHubMonitor,
    MonitoredComment,
)

router = APIRouter(prefix="/comments/v2", tags=["comment-hub-v2"])

# Singleton instance
_monitor = CommentHubMonitor()


# ─── Schemas ───

class FetchCommentsRequest(BaseModel):
    content_id: str
    account_id: str
    count: int = 20


class CommentOut(BaseModel):
    id: str
    content_id: str
    account_id: str
    author_id: str
    text: str
    sentiment: str
    created_at: str


class ReplyStrategyOut(BaseModel):
    rule_id: str
    rule_name: str
    reply: str
    action: str
    matched_keywords: List[str]


class AlertRuleCreate(BaseModel):
    account_id: Optional[str] = None
    content_id: Optional[str] = None
    negative_threshold: float = 0.3
    min_comment_count: int = 10
    window_minutes: int = 60


class AlertOut(BaseModel):
    id: str
    rule_id: str
    level: str
    message: str
    negative_ratio: float
    total_comments: int
    created_at: str


class SentimentTrendOut(BaseModel):
    content_id: str
    total_comments: int
    positive_ratio: float
    neutral_ratio: float
    negative_ratio: float
    trend: str  # improving | stable | worsening


# ─── Helpers ───

def _comment_to_out(c: MonitoredComment) -> CommentOut:
    return CommentOut(
        id=c.id,
        content_id=c.content_id,
        account_id=c.account_id,
        author_id=c.author_id,
        text=c.text,
        sentiment=c.sentiment,
        created_at=c.created_at,
    )


def _alert_to_out(a: Alert) -> AlertOut:
    return AlertOut(
        id=a.id,
        rule_id=a.rule_id,
        level=a.level,
        message=a.message,
        negative_ratio=a.negative_ratio,
        total_comments=a.total_comments,
        created_at=a.created_at,
    )


# ─── Routes: Comment Monitor ───

@router.post("/monitor/fetch", response_model=List[CommentOut])
async def fetch_comments_route(req: FetchCommentsRequest, user=Depends(get_current_user)):
    """Fetch and monitor comments for a content item."""
    comments = _monitor.monitor.fetch_comments(
        content_id=req.content_id,
        account_id=req.account_id,
        count=req.count,
    )
    return [_comment_to_out(c) for c in comments]


@router.get("/monitor/list")
async def list_comments_route(
    content_id: Optional[str] = None,
    account_id: Optional[str] = None,
    sentiment: Optional[str] = None,
    user=Depends(get_current_user),
):
    """List monitored comments with filters."""
    comments = _monitor.monitor.list_comments(content_id, account_id, sentiment)
    return [_comment_to_out(c) for c in comments]


# ─── Routes: Reply Strategy ───

@router.post("/strategy/analyze")
async def analyze_reply_strategy(
    comment_text: str,
    sentiment: str = "neutral",
    user=Depends(get_current_user),
):
    """Analyze a comment and suggest reply strategy."""
    result = _monitor.strategy.generate_reply(comment_text, sentiment)
    if not result:
        return {"matched": False, "message": "No matching rule"}
    return {"matched": True, **result}


@router.get("/strategy/rules")
async def list_reply_rules(user=Depends(get_current_user)):
    """List all active reply strategy rules."""
    rules = _monitor.strategy.list_rules()
    return [
        {
            "id": r.id,
            "name": r.name,
            "keywords": r.keywords,
            "sentiment": r.sentiment,
            "reply_template": r.reply_template,
            "action": r.action,
            "priority": r.priority,
        }
        for r in rules
    ]


# ─── Routes: Sentiment Alert ───

@router.post("/alert-rules")
async def create_alert_rule(req: AlertRuleCreate, user=Depends(get_current_user)):
    """Create a sentiment alert rule."""
    import secrets
    rule = AlertRule(
        id=f"ar_{secrets.token_urlsafe(6)}",
        account_id=req.account_id,
        content_id=req.content_id,
        negative_threshold=req.negative_threshold,
        min_comment_count=req.min_comment_count,
        window_minutes=req.window_minutes,
    )
    _monitor.alert.add_rule(rule)
    return {"id": rule.id, "message": "Alert rule created"}


@router.get("/alert-rules")
async def list_alert_rules(user=Depends(get_current_user)):
    """List all sentiment alert rules."""
    rules = _monitor.alert.list_rules()
    return [
        {
            "id": r.id,
            "account_id": r.account_id,
            "content_id": r.content_id,
            "negative_threshold": r.negative_threshold,
            "min_comment_count": r.min_comment_count,
            "window_minutes": r.window_minutes,
            "enabled": r.enabled,
        }
        for r in rules
    ]


@router.post("/alerts/evaluate")
async def evaluate_alerts(rule_id: Optional[str] = None, user=Depends(get_current_user)):
    """Evaluate current comments against alert rules."""
    comments = list(_monitor.monitor._comments.values())
    alerts = _monitor.alert.evaluate(comments, rule_id)
    return [_alert_to_out(a) for a in alerts]


@router.get("/alerts")
async def list_alerts(
    level: Optional[str] = None,
    account_id: Optional[str] = None,
    user=Depends(get_current_user),
):
    """List generated alerts."""
    alerts = _monitor.alert.list_alerts(level, account_id)
    return [_alert_to_out(a) for a in alerts]


@router.get("/sentiment-trend/{content_id}")
async def get_sentiment_trend(content_id: str, user=Depends(get_current_user)):
    """Get sentiment trend for a content item."""
    comments = _monitor.monitor.list_comments(content_id=content_id)
    total = len(comments)
    if total == 0:
        return SentimentTrendOut(
            content_id=content_id,
            total_comments=0,
            positive_ratio=0.0,
            neutral_ratio=0.0,
            negative_ratio=0.0,
            trend="stable",
        )

    pos = sum(1 for c in comments if c.sentiment == "positive")
    neg = sum(1 for c in comments if c.sentiment == "negative")
    neu = total - pos - neg

    negative_ratio = neg / total
    trend = "stable"
    if negative_ratio > 0.3:
        trend = "worsening"
    elif negative_ratio < 0.1:
        trend = "improving"

    return SentimentTrendOut(
        content_id=content_id,
        total_comments=total,
        positive_ratio=round(pos / total, 2),
        neutral_ratio=round(neu / total, 2),
        negative_ratio=round(negative_ratio, 2),
        trend=trend,
    )
