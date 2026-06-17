"""TrendScout API — trend reports and persona clone drafts.

V2.7.1增强: PDF生成、5A匹配度、人群契合度、批量报告
"""

from typing import List, Optional, Literal
import secrets
from fastapi import APIRouter, Depends, Query, HTTPException, Body
from pydantic import BaseModel, ConfigDict

from src.api.auth import get_current_user
from src.core.database import get_db_optional
from src.services import trend_scout_service
from src.services import trend_scout_v2_service
import src.services.timeline_library_function as tlf
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/trend-scout", tags=["trend-scout"])


class TrendReportCreate(BaseModel):
    query: str
    stage_filter: str = ""
    items: Optional[List[dict]] = None
    source: Literal["mock", "import"] = "mock"
    tenant_id: Optional[str] = None


class TrendItemOut(BaseModel):
    rank: int
    note_id: str
    title: str
    title_structure: str
    ces_estimate: int
    traffic_pool: str
    stage: str
    tags: List[str]
    post_time: str
    post_day: str
    persona_signals: dict


class RiskSignalOut(BaseModel):
    signal: str
    severity: str
    source: str


class TrendReportOut(BaseModel):
    id: str
    query: str
    stage_filter: str
    crawl_time: str
    results: List[TrendItemOut]
    platform_risk_signals: List[RiskSignalOut]
    created_at: str
    source: str
    payload_json: Optional[dict]
    tenant_id: Optional[str]

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# V2.7.1 增强版数据模型
# =============================================================================

class TrendReportCreateV2(BaseModel):
    """V2报告创建请求."""
    query: str
    stage_filter: str = ""
    audience_segment_ids: List[str] = []
    items: Optional[List[dict]] = None
    source: Literal["mock", "import"] = "mock"
    tenant_id: Optional[str] = None


class RecommendedTopicOut(BaseModel):
    """推荐选题输出."""
    id: str
    topic_title: str
    stage_match: str  # 5A阶段
    stage_match_score: float
    audience_fit_score: float
    engagement_interval: dict
    risk_level: str


class TrendReportOutV2(TrendReportOut):
    """V2增强版报告输出."""
    audience_segment_ids: List[str]
    recommended_topics: List[RecommendedTopicOut]
    report_html: Optional[str]
    report_pdf_url: Optional[str]
    target_audience: Optional[dict]
    brand_knowledge_refs: List[str]
    timeline_events: List[dict] = []

    model_config = ConfigDict(from_attributes=True)


class PersonaDraftCreate(BaseModel):
    points: List[str]


class PersonaDraftOut(BaseModel):
    id: str
    identity_core: dict
    content_voice: dict
    content_preferences: dict
    warnings: List[str]
    status: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)


def _report_to_out(report: trend_scout_service.TrendReport) -> TrendReportOut:
    return TrendReportOut(
        id=report.id,
        query=report.query,
        stage_filter=report.stage_filter,
        crawl_time=report.crawl_time,
        results=[
            TrendItemOut(
                rank=r.rank, note_id=r.note_id, title=r.title,
                title_structure=r.title_structure, ces_estimate=r.ces_estimate,
                traffic_pool=r.traffic_pool, stage=r.stage, tags=r.tags,
                post_time=r.post_time, post_day=r.post_day,
                persona_signals=r.persona_signals,
            )
            for r in report.results
        ],
        platform_risk_signals=[
            RiskSignalOut(signal=rs.signal, severity=rs.severity, source=rs.source)
            for rs in report.platform_risk_signals
        ],
        created_at=report.created_at,
        source=report.source,
        payload_json=report.payload_json,
        tenant_id=report.tenant_id,
    )


def _topic_to_out(topic: trend_scout_v2_service.RecommendedTopic) -> RecommendedTopicOut:
    """转换推荐选题."""
    return RecommendedTopicOut(
        id=topic.id,
        topic_title=topic.topic_title,
        stage_match=topic.stage_match,
        stage_match_score=topic.stage_match_score,
        audience_fit_score=topic.audience_fit_score,
        engagement_interval=topic.engagement_interval,
        risk_level=topic.risk_level,
    )


def _report_v2_to_out(report: trend_scout_v2_service.TrendReportV2) -> TrendReportOutV2:
    """转换V2报告."""
    base = _report_to_out(report)
    return TrendReportOutV2(
        **base.model_dump(),
        audience_segment_ids=report.audience_segment_ids,
        recommended_topics=[_topic_to_out(t) for t in report.recommended_topics],
        report_html=report.report_html,
        report_pdf_url=report.report_pdf_url,
        target_audience=report.target_audience,
        brand_knowledge_refs=report.brand_knowledge_refs,
        timeline_events=report.timeline_events,
    )


@router.post("/reports", status_code=201, response_model=TrendReportOutV2)
async def create_report(
    data: TrendReportCreateV2,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db_optional),
):
    """创建V2增强版趋势报告."""
    report = trend_scout_v2_service.create_trend_report_v2(
        query=data.query,
        stage_filter=data.stage_filter,
        audience_segment_ids=data.audience_segment_ids,
        items=data.items,
        source=data.source,
        tenant_id=data.tenant_id,
    )

    # W15: TimelineLibrary integration — fetch active seasonal events
    if db is not None:
        try:
            from datetime import datetime, timezone
            today = datetime.now(timezone.utc)
            events = await tlf.get_active_events_for_date(db, today)
            report.timeline_events = [
                {
                    "id": str(e.id),
                    "name": e.name,
                    "event_type": e.event_type,
                    "start_date": e.start_date.isoformat() if e.start_date else None,
                    "end_date": e.end_date.isoformat() if e.end_date else None,
                }
                for e in events
            ]
        except Exception:
            # Graceful degradation
            report.timeline_events = []

    return _report_v2_to_out(report)


@router.get("/reports")
def list_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user=Depends(get_current_user),
):
    reports = trend_scout_v2_service._report_db.values()
    all_reports = sorted(reports, key=lambda r: r.created_at, reverse=True)
    page = list(all_reports)[skip : skip + limit]
    return {
        "reports": [_report_v2_to_out(r) for r in page]
    }


@router.get("/reports/{report_id}", response_model=TrendReportOutV2)
def get_report(report_id: str, user=Depends(get_current_user)):
    report = trend_scout_v2_service.get_trend_report_v2(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return _report_v2_to_out(report)


@router.post("/persona-draft", status_code=201, response_model=PersonaDraftOut)
def create_persona_draft(data: PersonaDraftCreate, user=Depends(get_current_user)):
    draft = trend_scout_service.create_persona_draft(points=data.points)
    return PersonaDraftOut(
        id=draft.id,
        identity_core=draft.identity_core,
        content_voice=draft.content_voice,
        content_preferences=draft.content_preferences,
        warnings=draft.warnings,
        status=draft.status,
        created_at=draft.created_at,
    )


# =============================================================================
# V2.7.1 增强版路由
# =============================================================================

@router.post("/reports/{report_id}/generate-pdf")
def generate_report_pdf(report_id: str, user=Depends(get_current_user)):
    """生成PDF报告."""
    # 获取用户名
    username = getattr(user, 'username', 'anonymous') if hasattr(user, 'username') else 'anonymous'
    result = trend_scout_v2_service.generate_report_pdf(report_id, username)
    return result


@router.get("/reports/{report_id}/preview")
def preview_report(report_id: str, user=Depends(get_current_user)):
    """预览报告HTML."""
    report = trend_scout_v2_service.get_trend_report_v2(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    html = trend_scout_v2_service.generate_report_html(report)
    return {"html_content": html, "brand_logo": "瑞德医生"}


@router.get("/reports/{report_id}/download")
def download_report(report_id: str, user=Depends(get_current_user)):
    """下载PDF报告."""
    report = trend_scout_v2_service.get_trend_report_v2(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not report.report_pdf_url:
        raise HTTPException(status_code=400, detail="PDF not generated yet")
    return {
        "pdf_url": report.report_pdf_url,
        "content_type": "application/pdf",
        "disclaimer": "内部资料，禁止外传",
    }


@router.post("/reports/batch")
def batch_create_reports(
    data: dict = Body(...),
    user=Depends(get_current_user)
):
    """批量生成选题报告."""
    result = trend_scout_v2_service.batch_create_trend_reports(
        query=data.get("query"),
        stage_filter=data.get("stage_filter", ""),
        account_ids=data.get("account_ids", []),
        audience_segment_ids=data.get("audience_segment_ids", []),
    )
    return result


# ─── Topic Library & Stats Endpoints ───



_topic_db: dict = {}
_hot_keywords: list = [
    {"word": "猫咪掉毛", "heat_score": 98, "trend": "up"},
    {"word": "狗粮推荐", "heat_score": 95, "trend": "stable"},
    {"word": "宠物疫苗", "heat_score": 92, "trend": "up"},
    {"word": "驱虫攻略", "heat_score": 88, "trend": "down"},
    {"word": "新手养猫", "heat_score": 85, "trend": "up"},
    {"word": "猫砂测评", "heat_score": 82, "trend": "stable"},
    {"word": "狗狗训练", "heat_score": 78, "trend": "up"},
    {"word": "宠物保险", "heat_score": 75, "trend": "up"},
]


class TopicUpdateRequest(BaseModel):
    status: str


class TopicCreateRequest(BaseModel):
    title: str
    source_report_id: Optional[str] = None
    tags: List[str] = []


@router.get("/topics")
def list_topics(
    status: Optional[str] = None,
    user=Depends(get_current_user),
):
    """返回选题库列表."""
    topics = list(_topic_db.values())
    if status:
        topics = [t for t in topics if t.get("status") == status]
    # Ensure seed data exists
    if not topics:
        topics = [
            {
                "id": "topic-001",
                "title": "夏季猫咪防暑指南",
                "source_report": "report-001",
                "estimated_engagement": 350,
                "tags": ["猫咪", "夏季", "健康"],
                "status": "pending",
            },
            {
                "id": "topic-002",
                "title": "狗粮成分解析",
                "source_report": "report-002",
                "estimated_engagement": 280,
                "tags": ["狗粮", "成分", "测评"],
                "status": "adopted",
            },
            {
                "id": "topic-003",
                "title": "新手养狗避坑清单",
                "source_report": "report-003",
                "estimated_engagement": 420,
                "tags": ["新手", "狗狗", "避坑"],
                "status": "pending",
            },
        ]
        for t in topics:
            _topic_db[t["id"]] = t
    return {"topics": topics}


@router.patch("/topics/{topic_id}")
def update_topic_status(
    topic_id: str,
    req: TopicUpdateRequest,
    user=Depends(get_current_user),
):
    """更新选题状态."""
    topic = _topic_db.get(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    topic["status"] = req.status
    return topic


@router.delete("/topics/{topic_id}", status_code=204)
def delete_topic(
    topic_id: str,
    user=Depends(get_current_user),
):
    """删除选题."""
    if topic_id not in _topic_db:
        raise HTTPException(status_code=404, detail="Topic not found")
    del _topic_db[topic_id]
    return None


@router.post("/topics", status_code=201)
def create_topic(
    req: TopicCreateRequest,
    user=Depends(get_current_user),
):
    """从报告创建选题."""
    topic_id = f"topic-{secrets.token_urlsafe(8)}"
    topic = {
        "id": topic_id,
        "title": req.title,
        "source_report": req.source_report_id,
        "estimated_engagement": 200 + (hash(topic_id) % 300),
        "tags": req.tags,
        "status": "pending",
    }
    _topic_db[topic_id] = topic
    return topic


@router.get("/hot-keywords")
def get_hot_keywords(user=Depends(get_current_user)):
    """返回热词列表."""
    return {"keywords": _hot_keywords}


@router.get("/stats")
def get_stats(user=Depends(get_current_user)):
    """返回统计."""
    return {
        "total_reports": 24,
        "weekly_new": 5,
        "hot_topics": 8,
        "adopted_topics": 12,
    }
