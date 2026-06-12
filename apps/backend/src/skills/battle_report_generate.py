"""Battle Report Generate Skill — v4.0 Phase 1 P1-3.

被 AI Copilot 调用，读取 EngagementORM 数据，
通过 LLM Hub 生成战报文本。

替代原 DataAnalyst Agent 的战报生成逻辑。
单次调用，无 ReAct 循环。
"""

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.note_engagement_orm import NoteEngagementORM
from src.models.publish_task_orm import PublishTaskORM
from src.models.task_orm import TaskORM


@dataclass
class BattleReport:
    report_id: str
    title: str
    period: str
    summary: str
    highlights: List[Dict[str, str]]
    recommendations: List[str]
    raw_data: Dict
    created_at: str = ""


async def generate_battle_report(
    db: AsyncSession,
    account_id: Optional[str] = None,
    period_days: int = 7,
    tenant_id: str = "default",
) -> BattleReport:
    """Generate a battle report from engagement data.

    Reads NoteEngagementORM data and formats it into a report.
    MVP: Structured text report without LLM call.
    Production: Route through LLM Hub for polished report generation.
    """
    from sqlalchemy import func

    since = datetime.now(timezone.utc) - timedelta(days=period_days)

    # Query engagement data
    stmt = select(NoteEngagementORM).where(
        NoteEngagementORM.fetch_status == "success"
    ).where(NoteEngagementORM.created_at >= since)

    if account_id:
        stmt = stmt.where(NoteEngagementORM.account_id == account_id)

    result = await db.execute(stmt)
    records = result.scalars().all()

    if not records:
        return BattleReport(
            report_id=f"br_{secrets.token_urlsafe(12)}",
            title=f"近{period_days}日战报",
            period=f"{period_days}天",
            summary="暂无互动数据，请等待 engagement_collect 定时任务执行。",
            highlights=[],
            recommendations=["确认内容已发布且平台 API 可访问", "检查 engagement_collect 定时任务配置"],
            raw_data={"record_count": 0, "period_days": period_days},
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    # Aggregate metrics
    total_likes = sum(r.likes or 0 for r in records)
    total_comments = sum(r.comments or 0 for r in records)
    total_saves = sum(r.saves or 0 for r in records)
    total_shares = sum(r.shares or 0 for r in records)
    total_views = sum(r.views or 0 for r in records)
    record_count = len(records)

    avg_likes = total_likes / record_count
    avg_comments = total_comments / record_count
    avg_saves = total_saves / record_count
    avg_views = total_views / record_count

    # Find top performing post
    top_post = max(records, key=lambda r: (r.likes or 0) + (r.comments or 0) + (r.saves or 0))

    # Build highlights
    highlights = [
        {
            "metric": "总点赞",
            "value": str(total_likes),
            "trend": "↑" if total_likes > record_count * 100 else "→",
        },
        {
            "metric": "总收藏",
            "value": str(total_saves),
            "trend": "↑" if total_saves > record_count * 50 else "→",
        },
        {
            "metric": "总评论",
            "value": str(total_comments),
            "trend": "↑" if total_comments > record_count * 20 else "→",
        },
        {
            "metric": "平均互动率",
            "value": f"{((avg_likes + avg_comments + avg_saves) / max(avg_views, 1) * 100):.2f}%",
            "trend": "→",
        },
    ]

    # Generate recommendations
    recommendations = []
    if avg_saves > avg_likes * 0.5:
        recommendations.append("收藏率较高，建议增加干货类内容")
    if avg_comments < avg_likes * 0.1:
        recommendations.append("评论率偏低，可在内容中增加互动提问")
    if total_shares < record_count * 5:
        recommendations.append("分享量较少，建议优化标题和封面提升传播性")
    if not recommendations:
        recommendations.append("整体表现良好，建议保持当前内容策略")

    summary = (
        f"近{period_days}日共发布 {record_count} 篇内容，"
        f"累计获得 {total_likes} 点赞、{total_saves} 收藏、{total_comments} 评论。"
        f"平均互动率 {((avg_likes + avg_comments + avg_saves) / max(avg_views, 1) * 100):.2f}%。"
    )

    if top_post.platform_post_id:
        summary += f" 最佳表现内容 ID: {top_post.platform_post_id}。"

    return BattleReport(
        report_id=f"br_{secrets.token_urlsafe(12)}",
        title=f"近{period_days}日战报",
        period=f"{period_days}天",
        summary=summary,
        highlights=highlights,
        recommendations=recommendations,
        raw_data={
            "record_count": record_count,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_saves": total_saves,
            "total_shares": total_shares,
            "total_views": total_views,
            "avg_likes": round(avg_likes, 2),
            "avg_comments": round(avg_comments, 2),
            "avg_saves": round(avg_saves, 2),
            "top_post_id": top_post.platform_post_id,
            "period_days": period_days,
        },
        created_at=datetime.now(timezone.utc).isoformat(),
    )


async def generate_battle_report_for_content(
    db: AsyncSession,
    content_id: str,
    tenant_id: str = "default",
) -> Optional[BattleReport]:
    """Generate a battle report for a specific content item.

    Finds the publish task and engagement data for the given content_id.
    """
    # Find publish task for content
    stmt = (
        select(PublishTaskORM)
        .where(PublishTaskORM.draft_id == content_id)
        .where(PublishTaskORM.status == "published")
        .order_by(PublishTaskORM.published_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    publish_task = result.scalar_one_or_none()

    if not publish_task or not publish_task.platform_post_id:
        return None

    # Find engagement records
    stmt2 = (
        select(NoteEngagementORM)
        .where(NoteEngagementORM.publish_task_id == publish_task.id)
        .where(NoteEngagementORM.fetch_status == "success")
        .order_by(NoteEngagementORM.fetched_at.desc())
    )
    result2 = await db.execute(stmt2)
    records = result2.scalars().all()

    if not records:
        return None

    latest = records[0]
    total_likes = sum(r.likes or 0 for r in records)
    total_comments = sum(r.comments or 0 for r in records)
    total_saves = sum(r.saves or 0 for r in records)

    highlights = [
        {"metric": "点赞", "value": str(latest.likes or 0), "trend": "→"},
        {"metric": "收藏", "value": str(latest.saves or 0), "trend": "→"},
        {"metric": "评论", "value": str(latest.comments or 0), "trend": "→"},
    ]

    return BattleReport(
        report_id=f"br_{secrets.token_urlsafe(12)}",
        title=f"内容战报: {content_id}",
        period="全周期",
        summary=(
            f"内容 {content_id} 累计获得 {total_likes} 点赞、"
            f"{total_saves} 收藏、{total_comments} 评论。"
            f"最新数据（{latest.fetched_at.isoformat() if latest.fetched_at else 'N/A'}）: "
            f"点赞 {latest.likes or 0}，收藏 {latest.saves or 0}，评论 {latest.comments or 0}。"
        ),
        highlights=highlights,
        recommendations=["持续监控互动趋势", "对比同类型内容表现"],
        raw_data={
            "content_id": content_id,
            "publish_task_id": publish_task.id,
            "platform_post_id": publish_task.platform_post_id,
            "record_count": len(records),
            "latest": {
                "likes": latest.likes,
                "comments": latest.comments,
                "saves": latest.saves,
                "shares": latest.shares,
                "views": latest.views,
                "fetched_at": latest.fetched_at.isoformat() if latest.fetched_at else None,
            },
        },
        created_at=datetime.now(timezone.utc).isoformat(),
    )
