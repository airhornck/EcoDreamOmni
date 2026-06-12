"""TrendScout — trend侦察服务.

MVP: Mock trend reports + persona clone drafts.
Production: Real crawler with platform signatures.
"""

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class TrendItem:
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
    persona_signals: Dict


@dataclass
class RiskSignal:
    signal: str
    severity: str
    source: str


@dataclass
class TrendReport:
    id: str
    query: str
    stage_filter: str
    crawl_time: str
    results: List[TrendItem]
    platform_risk_signals: List[RiskSignal]
    created_at: str = ""
    source: str = "mock"
    payload_json: Optional[Dict] = None
    tenant_id: Optional[str] = None


@dataclass
class PersonaDraft:
    id: str
    identity_core: Dict
    content_voice: Dict
    content_preferences: Dict
    status: str = "draft"
    created_at: str = ""
    warnings: List[str] = field(default_factory=list)


_report_db: Dict[str, TrendReport] = {}
_draft_db: Dict[str, PersonaDraft] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_trend_report(
    query: str,
    stage_filter: str = "",
    items: Optional[List[Dict]] = None,
    source: str = "mock",
    tenant_id: Optional[str] = None,
) -> TrendReport:
    report_id = secrets.token_urlsafe(12)

    if items and source == "import":
        result_items = []
        for idx, item in enumerate(items, 1):
            result_items.append(
                TrendItem(
                    rank=idx,
                    note_id=item.get("note_id", f"import_{idx}"),
                    title=item.get("title", ""),
                    title_structure=item.get("title_structure", ""),
                    ces_estimate=item.get("ces_estimate", 0),
                    traffic_pool=item.get("traffic_pool", ""),
                    stage=item.get("stage", ""),
                    tags=item.get("tags", []),
                    post_time=item.get("post_time", ""),
                    post_day=item.get("post_day", ""),
                    persona_signals=item.get("persona_signals", {}),
                )
            )
        payload_json = {"item_count": len(result_items), "query": query}
    else:
        mock_items = [
            TrendItem(
                rank=1,
                note_id="note_001",
                title=f"3个{query}误区，第2个我踩了2年",
                title_structure="数字+痛点+时间跨度",
                ces_estimate=85,
                traffic_pool="L4",
                stage="INTEREST",
                tags=[query, "新手养猫", "养猫经验"],
                post_time="20:00",
                post_day="周三",
                persona_signals={"pet_type": "cat", "owner_type": "租房年轻女性", "voice": "亲切吐槽"},
            ),
            TrendItem(
                rank=2,
                note_id="note_002",
                title=f"姐妹们谁懂啊，{query}真的太坑了",
                title_structure="情绪共鸣+痛点",
                ces_estimate=72,
                traffic_pool="L3",
                stage="AWARENESS",
                tags=[query, "吐槽", "真实经历"],
                post_time="12:00",
                post_day="周五",
                persona_signals={"pet_type": "cat", "owner_type": "多宠家庭", "voice": "真实吐槽"},
            ),
            TrendItem(
                rank=3,
                note_id="note_003",
                title=f"{query}避坑指南，新手必看",
                title_structure="痛点+受众定位",
                ces_estimate=68,
                traffic_pool="L3",
                stage="AWARENESS",
                tags=[query, "避坑", "指南"],
                post_time="21:00",
                post_day="周六",
                persona_signals={"pet_type": "cat", "owner_type": "学生党", "voice": "经验分享"},
            ),
        ]
        result_items = mock_items
        payload_json = None

    report = TrendReport(
        id=report_id,
        query=query,
        stage_filter=stage_filter or "ALL",
        crawl_time=_now(),
        results=result_items,
        platform_risk_signals=[
            RiskSignal(signal=f"近期'{query}'关键词审核加严", severity="medium", source="内容下架率异常"),
        ],
        created_at=_now(),
        source=source,
        payload_json=payload_json,
        tenant_id=tenant_id,
    )
    _report_db[report_id] = report
    return report


def list_trend_reports(skip: int = 0, limit: int = 100) -> List[TrendReport]:
    all_reports = sorted(_report_db.values(), key=lambda r: r.created_at, reverse=True)
    return all_reports[skip : skip + limit]


def get_trend_report(report_id: str) -> Optional[TrendReport]:
    return _report_db.get(report_id)


def create_persona_draft(points: List[str]) -> PersonaDraft:
    draft_id = secrets.token_urlsafe(12)
    warnings: List[str] = []

    # LLM unavailable fallback: rule template assembly
    warnings.append("LLM unavailable: using rule template assembly")

    draft = PersonaDraft(
        id=draft_id,
        identity_core={
            "nickname_pattern": "{pet_name}和它的铲屎官",
            "bio": "租房养猫3年 | 英短奶茶 | 分享真实踩坑经验",
            "gender": "female",
            "age_range": "25-30",
            "location": {"city": "上海", "district": "浦东新区", "housing_type": "租房一居室"},
        },
        content_voice={
            "tone": "亲切吐槽风",
            "formality_level": "very_casual",
            "emoji_frequency": "high",
            "emoji_style": ["😿", "😹", "💩", "👀", "✨"],
            "catchphrases": ["姐妹们谁懂啊", "真的服了", "亲测有效"],
            "sentence_length_preference": "short",
        },
        content_preferences={
            "preferred_topics": [
                {"topic": p, "expertise_level": "intermediate", "passion_level": "high"}
                for p in (points[:2] if points else ["驱虫避坑", "肠胃调理"])
            ],
            "avoid_topics": ["繁殖", "品种鄙视", "医疗诊断"],
        },
        status="draft",
        created_at=_now(),
        warnings=warnings,
    )
    _draft_db[draft_id] = draft
    return draft


def get_persona_draft(draft_id: str) -> Optional[PersonaDraft]:
    return _draft_db.get(draft_id)


def clear_trend_scout() -> None:
    _report_db.clear()
    _draft_db.clear()
