"""DataAnalyst API — reports, dashboard, attribution, calibration."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import get_current_user
from src.core.database import get_db
from src.models.note_engagement_orm import NoteEngagementORM
from src.models.publish_task_orm import PublishTaskORM
from src.models.task_orm import TaskORM
from src.services import data_analyst_service
from src.functions.engagement_collect import collect_all_pending_engagements, get_engagement_summary
from src.skills.battle_report_generate import generate_battle_report, generate_battle_report_for_content

router = APIRouter(prefix="/data-analyst", tags=["data-analyst"])


class ReportCreate(BaseModel):
    account_id: str
    content_id: str
    predicted_ces: float
    predicted_pool: str = "L2"
    period: str = "24h"


class ReportOut(BaseModel):
    id: str
    account_id: str
    content_id: str
    period: str
    actual_metrics: dict
    prediction_comparison: dict
    attribution: dict
    model_calibration: dict
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class ReportBatchOut(BaseModel):
    count: int
    reports: List[ReportOut]


class DashboardOut(BaseModel):
    has_data: bool
    guide: Optional[str] = None
    totalPublished: int
    totalPublishedChange: float
    avgCoverage: float
    avgMape: float
    avgLikes: float
    avgLikesChange: float


class AttributionOut(BaseModel):
    content_id: str
    prediction_comparison: dict
    top_features: List[dict]


class CalibrationJobOut(BaseModel):
    job_id: str
    status: str
    message: str


def _report_to_out(report: data_analyst_service.DataReport) -> ReportOut:
    return ReportOut(
        id=report.id,
        account_id=report.account_id,
        content_id=report.content_id,
        period=report.period,
        actual_metrics=report.actual_metrics,
        prediction_comparison=report.prediction_comparison,
        attribution=report.attribution,
        model_calibration=report.model_calibration,
        created_at=report.created_at,
    )


@router.post("/reports", status_code=201)
async def create_report(
    request: Request,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content_type = request.headers.get("content-type", "")

    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        file = form.get("file")
        if not file or not hasattr(file, "file"):
            raise HTTPException(status_code=400, detail="Missing CSV file")

        account_id = str(form.get("account_id", ""))
        predicted_ces_str = form.get("predicted_ces")
        predicted_ces = float(predicted_ces_str) if predicted_ces_str else None
        predicted_pool = str(form.get("predicted_pool", "L2"))
        period = str(form.get("period", "24h"))

        content = await file.read()
        try:
            reports = data_analyst_service.import_csv_reports(
                file_content=content,
                account_id=account_id,
                predicted_ces=predicted_ces,
                predicted_pool=predicted_pool,
                period=period,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        return ReportBatchOut(
            count=len(reports),
            reports=[_report_to_out(r) for r in reports],
        )
    else:
        body = await request.json()
        try:
            data = ReportCreate(**body)
        except Exception as e:
            raise HTTPException(status_code=422, detail=str(e))

        # Try to fetch real engagement data from NoteEngagementORM
        engagement = await _fetch_engagement_for_content(db, data.content_id)

        if engagement:
            # Real data available → compute report from actuals
            report = data_analyst_service.generate_data_report_from_actuals(
                account_id=data.account_id,
                content_id=data.content_id,
                actual_likes=engagement.get("likes") or 0,
                actual_comments=engagement.get("comments") or 0,
                actual_saves=engagement.get("saves") or 0,
                predicted_ces=data.predicted_ces,
                predicted_pool=data.predicted_pool,
                period=data.period,
            )
        else:
            # Fallback to mock data (MVP default)
            report = data_analyst_service.generate_data_report(
                account_id=data.account_id,
                content_id=data.content_id,
                predicted_ces=data.predicted_ces,
                predicted_pool=data.predicted_pool,
                period=data.period,
            )
        return _report_to_out(report)


async def _fetch_engagement_for_content(db: AsyncSession, content_id: str) -> dict | None:
    """Query NoteEngagementORM via PublishTaskORM.draft_id → content_id mapping.

    Returns engagement metrics dict or None if no real data exists.
    """
    # 1. Find published XHS task for this content draft
    stmt = (
        select(PublishTaskORM)
        .where(PublishTaskORM.draft_id == content_id)
        .where(PublishTaskORM.platform == "xhs")
        .where(PublishTaskORM.status == "published")
        .order_by(PublishTaskORM.published_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    publish_task = result.scalar_one_or_none()
    if not publish_task:
        return None

    # 2. Find successful engagement record
    stmt2 = (
        select(NoteEngagementORM)
        .where(NoteEngagementORM.publish_task_id == publish_task.id)
        .where(NoteEngagementORM.fetch_status == "success")
        .order_by(NoteEngagementORM.fetched_at.desc())
        .limit(1)
    )
    result2 = await db.execute(stmt2)
    record = result2.scalar_one_or_none()
    if not record:
        return None

    return {
        "likes": record.likes,
        "comments": record.comments,
        "saves": record.saves,
        "shares": record.shares,
        "views": record.views,
    }


@router.get("/reports", response_model=ReportBatchOut)
def list_reports(user=Depends(get_current_user)):
    reports = data_analyst_service.list_data_reports()
    return ReportBatchOut(
        count=len(reports),
        reports=[_report_to_out(r) for r in reports],
    )


@router.get("/reports/{report_id}", response_model=ReportOut)
def get_report(report_id: str, user=Depends(get_current_user)):
    report = data_analyst_service.get_data_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return _report_to_out(report)


@router.get("/dashboard", response_model=DashboardOut)
async def get_dashboard(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # v4.0: Use engagement_collect Function instead of in-memory mock
    summary = await get_engagement_summary(db, days=30)
    if not summary["has_data"]:
        # Fallback to legacy service for backward compatibility
        legacy = data_analyst_service.get_dashboard_summary()
        return DashboardOut(
            has_data=legacy["has_data"],
            guide=legacy.get("guide"),
            totalPublished=legacy["totalPublished"],
            totalPublishedChange=legacy["totalPublishedChange"],
            avgCoverage=legacy["avgCoverage"],
            avgMape=legacy["avgMape"],
            avgLikes=legacy["avgLikes"],
            avgLikesChange=legacy["avgLikesChange"],
        )
    return DashboardOut(
        has_data=True,
        guide=None,
        totalPublished=summary["total_records"],
        totalPublishedChange=0.0,
        avgCoverage=0.0,
        avgMape=0.0,
        avgLikes=summary["avg_likes"],
        avgLikesChange=0.0,
    )


@router.get("/attribution/{content_id}", response_model=AttributionOut)
def get_attribution(content_id: str, user=Depends(get_current_user)):
    report = data_analyst_service.get_report_by_content_id(content_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found for content_id")
    return AttributionOut(
        content_id=report.content_id,
        prediction_comparison=report.prediction_comparison,
        top_features=report.attribution.get("top_features", []),
    )


@router.post("/collect-engagements")
async def trigger_engagement_collection(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """手动触发 engagement 数据收集（v4.0 新增）."""
    summary = await collect_all_pending_engagements(db)
    return {"code": "OK", "message": "数据收集完成", "data": summary}


@router.post("/battle-report")
async def create_battle_report(
    period_days: int = 7,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """生成战报（v4.0: 通过 battle_report_generate Skill）."""
    report = await generate_battle_report(db, period_days=period_days)
    return {
        "code": "OK",
        "message": "战报生成成功",
        "data": {
            "report_id": report.report_id,
            "title": report.title,
            "period": report.period,
            "summary": report.summary,
            "highlights": report.highlights,
            "recommendations": report.recommendations,
            "created_at": report.created_at,
        },
    }


@router.get("/battle-report/{content_id}")
async def get_battle_report_for_content(
    content_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取指定内容的战报."""
    report = await generate_battle_report_for_content(db, content_id=content_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"内容战报未找到: {content_id}")
    return {
        "code": "OK",
        "message": "查询成功",
        "data": {
            "report_id": report.report_id,
            "title": report.title,
            "period": report.period,
            "summary": report.summary,
            "highlights": report.highlights,
            "recommendations": report.recommendations,
            "created_at": report.created_at,
        },
    }


@router.post("/calibrate", status_code=201, response_model=CalibrationJobOut)
def create_calibration(user=Depends(get_current_user)):
    job = data_analyst_service.create_calibration_job()
    return CalibrationJobOut(
        job_id=job.id,
        status=job.status,
        message=job.message,
    )


@router.get("/calibration-check")
def calibration_check(user=Depends(get_current_user)):
    needs = data_analyst_service.check_calibration_needed()
    return {"needs_calibration": needs, "count": len(needs)}


# ─── Mock Analytics Endpoints ───

from datetime import datetime, timedelta


@router.get("/publish-trend")
def get_publish_trend(days: int = 30, user=Depends(get_current_user)):
    """返回近N日每日发布量趋势."""
    base = datetime.now().date()
    trend = []
    for i in range(days - 1, -1, -1):
        d = base - timedelta(days=i)
        count = 5 + (hash(d.isoformat()) % 15)
        trend.append({"date": d.isoformat(), "count": count})
    return {"trend": trend}


@router.get("/platform-distribution")
def get_platform_distribution(user=Depends(get_current_user)):
    """返回各平台内容占比."""
    distribution = [
        {"platform": "xhs", "count": 128, "percentage": 52.0},
        {"platform": "douyin", "count": 78, "percentage": 31.7},
        {"platform": "wechat_channels", "count": 40, "percentage": 16.3},
    ]
    return {"distribution": distribution}


@router.get("/engagement-distribution")
def get_engagement_distribution(user=Depends(get_current_user)):
    """返回互动量分布."""
    return {
        "likes_avg": 142.5,
        "comments_avg": 23.8,
        "collections_avg": 45.2,
    }


@router.get("/mape-trend")
def get_mape_trend(user=Depends(get_current_user)):
    """返回MAPE趋势."""
    base = datetime.now().date()
    trend = []
    for i in range(13, -1, -1):
        d = base - timedelta(days=i)
        mape = round(0.12 + (hash(d.isoformat()) % 20) / 100, 4)
        trend.append({"date": d.isoformat(), "mape": mape})
    return {"trend": trend}


@router.get("/content-ranking")
def get_content_ranking(limit: int = 10, user=Depends(get_current_user)):
    """返回内容排行."""
    ranking = []
    for i in range(1, limit + 1):
        ranking.append({
            "rank": i,
            "title": f"示例内容标题 #{i}",
            "platform": ["xhs", "douyin", "wechat_channels"][i % 3],
            "likes": 100 + i * 50,
            "comments": 20 + i * 10,
            "collections": 30 + i * 15,
            "coverage": round(0.7 + (i % 30) / 100, 2),
            "mape": round(0.1 + (i % 15) / 100, 4),
        })
    return {"ranking": ranking}


@router.get("/account-comparison")
def get_account_comparison(user=Depends(get_current_user)):
    """返回账号对比."""
    accounts = [
        {
            "account_id": "acc-xhs-001",
            "account_name": "素人养猫日记",
            "platform": "xhs",
            "avg_engagement": 245.6,
            "health_score": 92,
        },
        {
            "account_id": "acc-dy-002",
            "account_name": "狗狗健康小知识",
            "platform": "douyin",
            "avg_engagement": 189.3,
            "health_score": 87,
        },
        {
            "account_id": "acc-wc-003",
            "account_name": "宠物日常分享",
            "platform": "wechat_channels",
            "avg_engagement": 156.2,
            "health_score": 85,
        },
    ]
    return {"accounts": accounts}


@router.get("/calibration-status")
def get_calibration_status(user=Depends(get_current_user)):
    """返回校准状态."""
    return {
        "last_calibrated_at": (datetime.now() - timedelta(days=3)).isoformat(),
        "status": "ok",
        "mape_threshold": 0.25,
        "drift_detected": False,
    }


@router.get("/import-history")
def get_import_history(user=Depends(get_current_user)):
    """返回导入历史."""
    history = [
        {
            "id": "imp-001",
            "imported_at": (datetime.now() - timedelta(days=1)).isoformat(),
            "file_name": "reports_20250520.csv",
            "record_count": 42,
        },
        {
            "id": "imp-002",
            "imported_at": (datetime.now() - timedelta(days=5)).isoformat(),
            "file_name": "reports_20250515.csv",
            "record_count": 28,
        },
    ]
    return {"history": history}


@router.get("/engagement-trend")
def get_engagement_trend(days: int = 7, user=Depends(get_current_user)):
    """返回近N日互动量趋势."""
    base = datetime.now().date()
    trend = []
    for i in range(days - 1, -1, -1):
        d = base - timedelta(days=i)
        likes = 50 + (hash(d.isoformat()) % 200)
        comments = 10 + (hash(d.isoformat() + "c") % 50)
        collections = 20 + (hash(d.isoformat() + "s") % 80)
        trend.append({
            "date": d.isoformat(),
            "likes": likes,
            "comments": comments,
            "collections": collections,
        })
    return {"trend": trend}


# ─── Engagement Data Tracking Endpoints ───

class EngagementItemOut(BaseModel):
    id: str
    publish_task_id: str
    account_id: str
    platform_post_id: str
    likes: Optional[int] = None
    comments: Optional[int] = None
    saves: Optional[int] = None
    shares: Optional[int] = None
    views: Optional[int] = None
    fetch_status: str
    fetch_error: Optional[str] = None
    fetched_at: Optional[str] = None
    created_at: str
    # Enriched from related task
    task_name: Optional[str] = None
    content_title: Optional[str] = None
    published_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class EngagementListOut(BaseModel):
    total: int
    items: List[EngagementItemOut]


@router.get("/engagements", response_model=EngagementListOut)
async def list_engagements(
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List note engagement records with optional status filter.

    Returns engagement metrics enriched with task name and content title
    from the related TaskHub task (via publish_task_id → tasks.id).
    """
    # Build base query
    stmt = select(NoteEngagementORM)
    if status:
        stmt = stmt.where(NoteEngagementORM.fetch_status == status)
    stmt = stmt.order_by(NoteEngagementORM.created_at.desc())

    # Count total
    count_stmt = select(__import__("sqlalchemy").func.count()).select_from(NoteEngagementORM)
    if status:
        count_stmt = count_stmt.where(NoteEngagementORM.fetch_status == status)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    # Fetch paginated records
    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    records = result.scalars().all()

    # Enrich with task info
    items: List[EngagementItemOut] = []
    for rec in records:
        task_name = None
        content_title = None
        published_url = None

        # Try to find related TaskHub task by publish_task_id (tasks.id as string)
        if rec.publish_task_id:
            try:
                task_stmt = select(TaskORM).where(TaskORM.id.cast(String) == rec.publish_task_id)
                task_result = await db.execute(task_stmt)
                task = task_result.scalar_one_or_none()
                if task:
                    task_name = task.name
                    pv = task.prompt_variables or {}
                    gc = pv.get("generated_content", {}) if isinstance(pv, dict) else {}
                    content_title = gc.get("title") if isinstance(gc, dict) else None
                    # Try to find published_url from prompt_variables or execution context
                    publish_result = pv.get("publish_result", {}) if isinstance(pv, dict) else {}
                    if isinstance(publish_result, dict):
                        published_url = publish_result.get("url") or publish_result.get("published_url")
            except Exception:
                pass

            # Fallback: try PublishTaskORM
            if not task_name:
                try:
                    pt_stmt = select(PublishTaskORM).where(PublishTaskORM.id == rec.publish_task_id)
                    pt_result = await db.execute(pt_stmt)
                    pt = pt_result.scalar_one_or_none()
                    if pt:
                        task_name = pt.draft_id  # fallback identifier
                        published_url = pt.published_url
                except Exception:
                    pass

        # Build published URL from platform_post_id if not found
        if not published_url and rec.platform_post_id:
            published_url = f"https://www.xiaohongshu.com/explore/{rec.platform_post_id}"

        items.append(EngagementItemOut(
            id=rec.id,
            publish_task_id=rec.publish_task_id,
            account_id=rec.account_id,
            platform_post_id=rec.platform_post_id,
            likes=rec.likes,
            comments=rec.comments,
            saves=rec.saves,
            shares=rec.shares,
            views=rec.views,
            fetch_status=rec.fetch_status,
            fetch_error=rec.fetch_error,
            fetched_at=rec.fetched_at.isoformat() if rec.fetched_at else None,
            created_at=rec.created_at.isoformat() if rec.created_at else "",
            task_name=task_name,
            content_title=content_title,
            published_url=published_url,
        ))

    return EngagementListOut(total=total, items=items)

