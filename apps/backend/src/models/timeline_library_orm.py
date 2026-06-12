"""TimelineLibrary ORM model — W14 Foundation Function.

季节事件库、产品上市时间线、与CronHub/BrandKnowledge联动.
Aligned with PRD V3.1 §TimelineLibrary / TASK_V2.7.1 FUNC-4.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime, JSON, Index
)
from sqlalchemy.dialects.postgresql import UUID

from src.core.database import Base


class TimelineEventORM(Base):
    """营销时间线事件表 — 季节事件与商业主题管理."""

    __tablename__ = "timeline_events"
    __table_args__ = (
        Index("ix_te_tenant_dates", "tenant_id", "start_date", "end_date"),
        Index("ix_te_type_dates", "event_type", "start_date"),
        {"comment": "TimelineLibrary — PRD V3.1 §TimelineLibrary"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 事件基本信息
    name = Column(String(255), nullable=False)
    event_type = Column(
        String(50),
        nullable=False,
        comment="season | product_launch | holiday | campaign | custom",
    )
    description = Column(Text, nullable=True)

    # 时间配置
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    recurring = Column(Boolean, default=False, nullable=False)
    cron_expression = Column(
        String(100),
        nullable=True,
        comment="CronHub绑定表达式 — croniter格式",
    )
    cron_job_id = Column(
        String(64),
        nullable=True,
        comment="关联CronHub任务ID",
    )
    year = Column(Integer, nullable=True, comment="年份 — 非重复事件")

    # 关联外部真源
    brand_knowledge_ids = Column(JSON, default=list, comment="关联BrandKnowledge条目ID列表")
    product_ids = Column(JSON, default=list, comment="关联产品ID列表")
    prohibited_claims = Column(JSON, default=list, comment="期间禁用语 — 联动BrandKnowledge")

    # 商业标记 — 触发广告审核
    is_commercial = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="True = 商业主题，强制触发额外审核流程",
    )

    # 状态
    status = Column(
        String(20),
        nullable=False,
        default="ACTIVE",
        comment="ACTIVE | ARCHIVED | DRAFT",
    )

    # 元数据
    priority = Column(Integer, default=0, nullable=False, comment="排序优先级")
    color_code = Column(String(20), nullable=True, comment="前端展示色值")

    # 审计
    created_by = Column(String(100), nullable=True)
    tenant_id = Column(String(64), nullable=True, index=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
