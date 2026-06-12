"""Engagement Collect Function — v4.0 Phase 1 P1-3.

确定性 ETL 函数：定时从平台 API 抓取互动数据，
写入 NoteEngagementORM。

替代原 DataAnalyst Agent 的数据拉取逻辑。
"""

import secrets
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.note_engagement_orm import NoteEngagementORM
from src.models.publish_task_orm import PublishTaskORM


async def collect_engagement_for_task(
    db: AsyncSession,
    publish_task_id: str,
    platform_post_id: str,
    account_id: str,
) -> Optional[NoteEngagementORM]:
    """Collect engagement data for a single published task.

    MVP: Simulated data (no real platform API yet).
    Production: Call platform API to fetch actual metrics.
    """
    # Check if already collected within last 24h
    stmt = (
        select(NoteEngagementORM)
        .where(NoteEngagementORM.publish_task_id == publish_task_id)
        .where(NoteEngagementORM.fetch_status == "success")
        .order_by(NoteEngagementORM.fetched_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing and existing.fetched_at:
        if datetime.now(timezone.utc) - existing.fetched_at < timedelta(hours=24):
            return existing  # Skip: collected recently

    # MVP: Generate simulated engagement data
    # Production: Replace with actual platform API call
    simulated_likes = 50 + (hash(platform_post_id) % 500)
    simulated_comments = int(simulated_likes * 0.15)
    simulated_saves = int(simulated_likes * 0.25)
    simulated_shares = int(simulated_likes * 0.05)
    simulated_views = simulated_likes * 10 + (hash(platform_post_id) % 1000)

    engagement = NoteEngagementORM(
        id=f"ne_{secrets.token_urlsafe(12)}",
        publish_task_id=publish_task_id,
        account_id=account_id,
        platform_post_id=platform_post_id,
        likes=simulated_likes,
        comments=simulated_comments,
        saves=simulated_saves,
        shares=simulated_shares,
        views=simulated_views,
        fetch_status="success",
        fetch_error=None,
        fetched_at=datetime.now(timezone.utc),
        raw_response={
            "source": "simulated",
            "likes": simulated_likes,
            "comments": simulated_comments,
            "saves": simulated_saves,
            "shares": simulated_shares,
            "views": simulated_views,
        },
    )
    db.add(engagement)
    await db.commit()
    await db.refresh(engagement)
    return engagement


async def collect_all_pending_engagements(db: AsyncSession) -> Dict[str, int]:
    """Collect engagement data for all pending/failed records.

    Typically called by Celery Beat every 24h.
    Returns summary: {"collected": N, "failed": N, "skipped": N}
    """
    # Find all publish tasks that need engagement collection
    stmt = (
        select(PublishTaskORM)
        .where(PublishTaskORM.status == "published")
        .where(PublishTaskORM.platform == "xhs")
    )
    result = await db.execute(stmt)
    publish_tasks = result.scalars().all()

    summary = {"collected": 0, "failed": 0, "skipped": 0}

    for pt in publish_tasks:
        if not pt.platform_post_id:
            summary["skipped"] += 1
            continue

        try:
            existing_stmt = (
                select(NoteEngagementORM)
                .where(NoteEngagementORM.publish_task_id == pt.id)
                .where(NoteEngagementORM.fetch_status == "success")
                .order_by(NoteEngagementORM.fetched_at.desc())
                .limit(1)
            )
            existing_result = await db.execute(existing_stmt)
            existing = existing_result.scalar_one_or_none()

            if existing and existing.fetched_at:
                if datetime.now(timezone.utc) - existing.fetched_at < timedelta(hours=24):
                    summary["skipped"] += 1
                    continue

            await collect_engagement_for_task(
                db=db,
                publish_task_id=pt.id,
                platform_post_id=pt.platform_post_id,
                account_id=pt.account_id or "",
            )
            summary["collected"] += 1
        except Exception as e:
            # Log failure but continue
            summary["failed"] += 1
            # Create failed record for visibility
            failed = NoteEngagementORM(
                id=f"ne_{secrets.token_urlsafe(12)}",
                publish_task_id=pt.id,
                account_id=pt.account_id or "",
                platform_post_id=pt.platform_post_id or "",
                fetch_status="failed",
                fetch_error=str(e),
                fetched_at=datetime.now(timezone.utc),
            )
            db.add(failed)
            try:
                await db.commit()
            except Exception:
                await db.rollback()

    return summary


async def get_engagement_summary(
    db: AsyncSession,
    account_id: Optional[str] = None,
    days: int = 30,
) -> Dict:
    """Get aggregated engagement summary for dashboard."""
    from sqlalchemy import func

    since = datetime.now(timezone.utc) - timedelta(days=days)

    stmt = select(NoteEngagementORM).where(
        NoteEngagementORM.fetch_status == "success"
    ).where(NoteEngagementORM.created_at >= since)

    if account_id:
        stmt = stmt.where(NoteEngagementORM.account_id == account_id)

    result = await db.execute(stmt)
    records = result.scalars().all()

    if not records:
        return {
            "has_data": False,
            "guide": "暂无数据，请等待 engagement_collect 定时任务执行或手动触发。",
            "total_records": 0,
            "avg_likes": 0.0,
            "avg_comments": 0.0,
            "avg_saves": 0.0,
            "avg_shares": 0.0,
            "avg_views": 0.0,
        }

    total = len(records)
    avg_likes = sum(r.likes or 0 for r in records) / total
    avg_comments = sum(r.comments or 0 for r in records) / total
    avg_saves = sum(r.saves or 0 for r in records) / total
    avg_shares = sum(r.shares or 0 for r in records) / total
    avg_views = sum(r.views or 0 for r in records) / total

    return {
        "has_data": True,
        "total_records": total,
        "avg_likes": round(avg_likes, 2),
        "avg_comments": round(avg_comments, 2),
        "avg_saves": round(avg_saves, 2),
        "avg_shares": round(avg_shares, 2),
        "avg_views": round(avg_views, 2),
        "period_days": days,
    }
