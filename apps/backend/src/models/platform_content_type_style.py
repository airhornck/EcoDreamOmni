"""PlatformContentTypeStyle ORM model — v4.0 Phase 1 P1-1.

平台内容类型风格真源表：存储各平台+内容类型的风格 DNA、
Prompt 片段、推荐关键词、语气参数、结构模板等。

Aligned with docs/契约与数据/02-数据库ER图.md §2.3
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship

from src.core.database import Base


class PlatformContentTypeStyleORM(Base):
    """平台内容类型风格表 — v4.0 新增."""

    __tablename__ = "platform_content_type_styles"
    __table_args__ = (
        Index("idx_pcstyles_tenant_platform_type", "tenant_id", "platform_id", "content_type"),
        Index("idx_pcstyles_status", "status"),
        {"comment": "PlatformContentTypeStyle — 平台内容类型风格真源"},
    )

    style_id = Column(
        String(64),
        primary_key=True,
        comment="风格唯一标识（style_xxx）",
    )
    tenant_id = Column(
        String(64),
        nullable=False,
        index=True,
        comment="所属租户",
    )
    platform_id = Column(
        String(32),
        nullable=False,
        index=True,
        comment="平台标识: xhs | douyin | wechat_official | bilibili",
    )
    content_type = Column(
        String(32),
        nullable=False,
        index=True,
        comment="内容类型: note_image | note_video | video_clone | long_article",
    )

    # 7 个核心字段
    content_dna = Column(
        JSON,
        default=dict,
        comment="内容 DNA：{hook_types, structure_patterns, tone_presets}",
    )
    default_prompt_fragments = Column(
        JSON,
        default=list,
        comment='默认 Prompt 片段列表，如 ["语气亲切自然..."]',
    )
    recommended_keywords = Column(
        JSON,
        default=dict,
        comment="推荐关键词：{high_performing, trending, seasonal}",
    )
    tone_preset = Column(
        JSON,
        default=dict,
        comment="语气参数：{formality, enthusiasm, urgency, empathy}",
    )
    structure_template = Column(
        JSON,
        default=dict,
        comment="结构模板：{paragraphs, paragraph_1...}",
    )
    avg_engagement_rate = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="平均互动率",
    )
    sample_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="分析样本数",
    )
    is_ai_generated = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否由 AI 分析自动沉淀",
    )
    source_template_ids = Column(
        JSON,
        default=list,
        comment="来源 ContentTemplate ID 列表",
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

    # 关联
    content_templates = relationship(
        "ContentTemplateORM",
        back_populates="platform_content_type_style",
        cascade="all, delete-orphan",
        lazy="selectin",
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
