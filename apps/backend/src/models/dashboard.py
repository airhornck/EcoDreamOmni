"""Dashboard data models and in-memory store (MVP phase)."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4


@dataclass
class TodayOverview:
    tasksPending: int = 0
    briefsPending: int = 0
    contentsPendingReview: int = 0
    contentsPublished: int = 0
    engagementDelta: float = 0.0
    avgHealthScore: float = 0.0


@dataclass
class QuickAction:
    id: str
    label: str
    icon: str
    href: str
    badge: Optional[int] = None


@dataclass
class Alert:
    id: str
    level: str  # emergency, warning, info, success
    title: str
    message: str
    timestamp: str


@dataclass
class ActivityEntry:
    id: str
    actor: str
    action: str
    target: str
    timestamp: str


# In-memory dashboard store with seed data for MVP
_dashboard_data = {
    "overview": TodayOverview(
        tasksPending=10,
        briefsPending=15,
        contentsPendingReview=5,
        contentsPublished=8,
        engagementDelta=23.0,
        avgHealthScore=87.0,
    ),
    "quick_actions": [
        QuickAction(id="gen", label="内容锻造", icon="FileText", href="/content-forge", badge=10),
        QuickAction(id="pub", label="发布管理", icon="Send", href="/publisher", badge=15),
        QuickAction(id="review", label="合规审核", icon="ShieldCheck", href="/compliance", badge=5),
        QuickAction(id="report", label="数据报表", icon="BarChart3", href="/data-analyst"),
        QuickAction(id="account", label="账号池", icon="Settings", href="/account-pool"),
    ],
    "alerts": [
        Alert(
            id=str(uuid4()),
            level="emergency",
            title="账号触发验证码",
            message="账号 acc_003 触发验证码，已进入保护模式",
            timestamp=datetime.now(timezone.utc).isoformat(),
        ),
        Alert(
            id=str(uuid4()),
            level="warning",
            title="合规预检黄标",
            message="2篇内容合规预检黄标，建议修改后发布",
            timestamp=datetime.now(timezone.utc).isoformat(),
        ),
        Alert(
            id=str(uuid4()),
            level="info",
            title="养号期结束",
            message="新号 acc_008 养号期结束，可开始正常发布",
            timestamp=datetime.now(timezone.utc).isoformat(),
        ),
        Alert(
            id=str(uuid4()),
            level="success",
            title="流量预测模型更新",
            message="流量预测模型已更新，探索期精度提升 12%",
            timestamp=datetime.now(timezone.utc).isoformat(),
        ),
    ],
    "activity_log": [
        ActivityEntry(
            id=str(uuid4()),
            actor="张运营",
            action="生成了",
            target="5篇「猫咪驱虫」内容",
            timestamp=datetime.now(timezone.utc).isoformat(),
        ),
        ActivityEntry(
            id=str(uuid4()),
            actor="李合规",
            action="审核通过了",
            target="3篇内容",
            timestamp=datetime.now(timezone.utc).isoformat(),
        ),
        ActivityEntry(
            id=str(uuid4()),
            actor="系统",
            action="账号进入保护模式",
            target="acc_003 触发验证码",
            timestamp=datetime.now(timezone.utc).isoformat(),
        ),
        ActivityEntry(
            id=str(uuid4()),
            actor="张运营",
            action="向15个素人分发了",
            target="Brief",
            timestamp=datetime.now(timezone.utc).isoformat(),
        ),
    ],
}


def get_overview() -> TodayOverview:
    return _dashboard_data["overview"]


def get_quick_actions() -> List[QuickAction]:
    return _dashboard_data["quick_actions"]


def get_alerts(level: Optional[str] = None) -> List[Alert]:
    alerts = _dashboard_data["alerts"]
    if level:
        return [a for a in alerts if a.level == level]
    return alerts


def get_activity_log(limit: int = 20, offset: int = 0) -> tuple[List[ActivityEntry], int]:
    entries = _dashboard_data["activity_log"]
    total = len(entries)
    return entries[offset : offset + limit], total
