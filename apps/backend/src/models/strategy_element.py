"""StrategyElement ORM model — v4.0 Strategy Element Architecture.

策略元素真源表：原子化的内容策略组件，可独立使用、组合、复用。
"""

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, String, Text, Integer, Float, DateTime, JSON, Index

from src.core.database import Base


class ElementType(str, Enum):
    """策略元素类型枚举."""

    STRUCTURE_FRAMEWORK = "structure_framework"
    HOOK_PATTERN = "hook_pattern"
    BODY_STRUCTURE = "body_structure"
    CTA_PATTERN = "cta_pattern"
    KEYWORD_STRATEGY = "keyword_strategy"
    EMOTION_CURVE = "emotion_curve"
    ENGAGEMENT_FORMULA = "engagement_formula"
    SCENE_ANCHOR = "scene_anchor"
    PERSONA = "persona"
    PERSONA_STORY = "persona_story"
    CONTENT_SERIES = "content_series"
    TIMELINE_EVENT = "timeline_event"
    METHODOLOGY_STAGE = "methodology_stage"
    PLATFORM_STYLE = "platform_style"
    BRAND_KNOWLEDGE = "brand_knowledge"
    CUSTOM_FRAGMENT = "custom_fragment"


class ElementSource(str, Enum):
    """策略元素来源枚举."""

    MANUAL = "manual"
    VIRAL_ANALYZER = "viral_analyzer"
    AI_GENERATED = "ai_generated"
    SYSTEM = "system"


class ElementStatus(str, Enum):
    """策略元素状态枚举."""

    ACTIVE = "active"
    DEPRECATED = "deprecated"
    DRAFT = "draft"


class StrategyElementORM(Base):
    """策略元素真源表."""

    __tablename__ = "strategy_elements"
    __table_args__ = (
        Index("ix_se_tenant_type", "tenant_id", "element_type", "status"),
        Index("ix_se_tenant_platform", "tenant_id", "platform", "status"),
        Index(
            "ix_se_recommend",
            "tenant_id",
            "element_type",
            "platform",
            "methodology_stage_id",
            "status",
        ),
        {"comment": "StrategyElement — 策略元素真源表"},
    )

    element_id = Column(
        String(64),
        primary_key=True,
        comment="策略元素唯一标识 elem_xxx",
    )
    tenant_id = Column(
        String(64),
        nullable=False,
        index=True,
        comment="所属租户",
    )

    element_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="元素类型",
    )
    element_subtype = Column(
        String(50),
        nullable=True,
        index=True,
        comment="元素子类型",
    )

    name = Column(
        String(128),
        nullable=False,
        comment="元素名称",
    )
    description = Column(
        Text,
        nullable=True,
        comment="元素描述",
    )

    content = Column(
        JSON,
        nullable=False,
        comment="元素内容（Schema 由 element_type 定义）",
    )
    render_template = Column(
        Text,
        nullable=False,
        comment="Jinja2 渲染模板",
    )
    variables = Column(
        JSON,
        default=list,
        comment="变量定义 [{name, label, type, default_value}]",
    )

    source = Column(
        String(50),
        default="manual",
        comment="来源：manual|viral_analyzer|ai_generated|system",
    )
    source_content_id = Column(
        String(64),
        nullable=True,
        comment="关联的爆款笔记/源内容 ID",
    )
    source_element_ids = Column(
        JSON,
        default=list,
        comment="若由多个元素合并，记录来源元素 ID 列表",
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
        index=True,
        comment="关联方法论阶段",
    )
    category = Column(
        String(64),
        nullable=True,
        index=True,
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
    effectiveness_score = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="效果评分 0-100",
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
