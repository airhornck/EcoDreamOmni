"""Dashboard API routes: operations homepage data."""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.dependencies import get_current_user
from src.models.task_orm import TaskORM
from src.models.user import User
from src.services.cron_hub import list_dlq
from src.services.dashboard_service import (
    fetch_activity_log,
    fetch_alerts,
    fetch_overview,
    fetch_quick_actions,
)
from src.services import llm_hub

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# ─── Response Models ───


class TodayOverviewData(BaseModel):
    tasksPending: int
    briefsPending: int
    contentsPendingReview: int
    contentsPublished: int
    engagementDelta: float
    avgHealthScore: float


class TodayOverviewResponse(BaseModel):
    today: TodayOverviewData


class QuickActionItem(BaseModel):
    id: str
    label: str
    icon: str
    href: str
    badge: Optional[int] = None


class QuickActionsResponse(BaseModel):
    actions: List[QuickActionItem]


class AlertItem(BaseModel):
    id: str
    level: str
    title: str
    message: str
    timestamp: str


class AlertsResponse(BaseModel):
    alerts: List[AlertItem]


class ActivityEntryItem(BaseModel):
    id: str
    actor: str
    action: str
    target: str
    timestamp: str


class ActivityLogResponse(BaseModel):
    entries: List[ActivityEntryItem]
    total: int


# ─── Routes ───


@router.get("/overview", response_model=TodayOverviewResponse)
def overview(user: User = Depends(get_current_user)):
    data = fetch_overview()
    return TodayOverviewResponse(
        today=TodayOverviewData(
            tasksPending=data.tasksPending,
            briefsPending=data.briefsPending,
            contentsPendingReview=data.contentsPendingReview,
            contentsPublished=data.contentsPublished,
            engagementDelta=data.engagementDelta,
            avgHealthScore=data.avgHealthScore,
        )
    )


@router.get("/quick-actions", response_model=QuickActionsResponse)
def quick_actions(user: User = Depends(get_current_user)):
    actions = fetch_quick_actions()
    return QuickActionsResponse(
        actions=[
            QuickActionItem(
                id=a.id,
                label=a.label,
                icon=a.icon,
                href=a.href,
                badge=a.badge,
            )
            for a in actions
        ]
    )


@router.get("/alerts", response_model=AlertsResponse)
def alerts(
    level: Optional[str] = Query(None, description="Filter by alert level: emergency, warning, info, success"),
    user: User = Depends(get_current_user),
):
    items = fetch_alerts(level)
    return AlertsResponse(
        alerts=[
            AlertItem(
                id=a.id,
                level=a.level,
                title=a.title,
                message=a.message,
                timestamp=a.timestamp,
            )
            for a in items
        ]
    )


@router.get("/activity-log", response_model=ActivityLogResponse)
def activity_log(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
):
    entries, total = fetch_activity_log(limit, offset)
    return ActivityLogResponse(
        entries=[
            ActivityEntryItem(
                id=e.id,
                actor=e.actor,
                action=e.action,
                target=e.target,
                timestamp=e.timestamp,
            )
            for e in entries
        ],
        total=total,
    )


@router.get("/core-metrics")
async def core_metrics(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # 1. 待审核任务数: tasks.status = 'human_wait'
    pending_result = await db.execute(
        select(func.count()).select_from(TaskORM).where(TaskORM.status == "human_wait")
    )
    pending_review = pending_result.scalar() or 0

    # 2. 今日已发布数: tasks.status = 'completed' AND published_at >= today
    published_result = await db.execute(
        select(func.count()).select_from(TaskORM).where(
            TaskORM.status == "completed",
            TaskORM.published_at >= today_start,
        )
    )
    published_today = published_result.scalar() or 0

    # 3. 队列中任务数: tasks.status = 'queued'
    queued_result = await db.execute(
        select(func.count()).select_from(TaskORM).where(TaskORM.status == "queued")
    )
    queued_tasks = queued_result.scalar() or 0

    # 4. 失败/DLQ 数: tasks.status = 'failed' + DLQ items
    failed_result = await db.execute(
        select(func.count()).select_from(TaskORM).where(TaskORM.status == "failed")
    )
    failed_count = failed_result.scalar() or 0
    dlq_items = list_dlq(status="PENDING_REVIEW")
    failed_dlq = failed_count + len(dlq_items)

    # 5. 今日 Token 成本
    cost_summary = await llm_hub.get_cost_summary(db, period_days=1)
    token_cost_today = cost_summary.get("total_cost", 0.0)

    return {
        "metrics": {
            "pendingReview": pending_review,
            "publishedToday": published_today,
            "queuedTasks": queued_tasks,
            "failedDlq": failed_dlq,
            "tokenCostToday": round(token_cost_today, 2),
        }
    }
