"""StrategySet ORM model — v4.0 Strategy Element Architecture.

策略组合快照表：可复用的内容策略元素组合 + 默认变量值。
ContentTemplate 的演进形态。
"""

from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, Integer, DateTime, JSON, Index

from src.core.database import Base


class StrategySetORM(Base):
    """策略组合快照表 —— ContentTemplate 的演进."""

    __tablename__ = "strategy_sets"
    __table_args__ = (
        Index("ix_ss_tenant_status", "tenant_id", "status"),
        Index("ix_ss_tenant_platform", "tenant_id", "platform", "status"),
        {"comment": "StrategySet — 策略组合快照"},
    )

    set_id = Column(
        String(64),
        primary_key=True,
        comment="策略组合唯一标识 set_xxx",
    )
    tenant_id = Column(
        String(64),
        nullable=False,
        index=True,
        comment="所属租户",
    )

    name = Column(
        String(128),
        nullable=False,
        comment="策略组合名称",
    )
    description = Column(
        Text,
        nullable=True,
        comment="策略组合描述",
    )

    element_refs = Column(
        JSON,
        nullable=False,
        comment="策略元素引用列表 [{element_id, priority, override_variables}]",
    )
    default_variables = Column(
        JSON,
        default=dict,
        comment="默认变量值",
    )

    source = Column(
        String(50),
        default="manual",
        comment="来源：manual|viral_analyzer|ai_generated",
    )
    source_content_id = Column(
        String(64),
        nullable=True,
        comment="关联的爆款笔记/源内容 ID",
    )

    platform = Column(
        String(32),
        nullable=True,
        index=True,
        comment="适用平台",
    )
    content_format = Column(
        String(32),
        nullable=True,
        comment="适用内容格式",
    )
    methodology_stage_id = Column(
        String(64),
        nullable=True,
        comment="关联方法论阶段",
    )
    category = Column(
        String(64),
        nullable=True,
        comment="内容分类",
    )

    usage_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="使用次数",
    )
    avg_engagement = Column(
        JSON,
        default=dict,
        comment="平均互动数据",
    )

    status = Column(
        String(32),
        default="active",
        nullable=False,
        index=True,
        comment="active | deprecated | draft",
    )

    created_by = Column(
        String(64),
        nullable=False,
        comment="创建者",
    )

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
