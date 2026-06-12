"""ContentTemplate ORM model — v4.0 Phase 1 P1-2.

内容模板真源表：存储从爆款内容解析出的结构模板、
Prompt 模板、变量定义、互动基准数据等。

Aligned with docs/契约与数据/02-数据库ER图.md §2.3
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    DateTime,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from src.core.database import Base


class ContentTemplateORM(Base):
    """内容模板表 — v4.0 新增."""

    __tablename__ = "content_templates"
    __table_args__ = (
        Index("idx_ctemplates_tenant_status", "tenant_id", "status"),
        Index("idx_ctemplates_style", "platform_content_type_style_id"),
        {"comment": "ContentTemplate — 内容模板真源"},
    )

    template_id = Column(
        String(64),
        primary_key=True,
        comment="模板唯一标识（tmpl_xxx）",
    )
    tenant_id = Column(
        String(64),
        nullable=False,
        index=True,
        comment="所属租户",
    )
    source_platform_id = Column(
        String(32),
        nullable=False,
        comment="来源平台",
    )
    source_content_url = Column(
        String(512),
        nullable=True,
        comment="源爆款链接",
    )
    source_content_id = Column(
        String(64),
        nullable=True,
        comment="源内容 ID",
    )
    source = Column(
        String(50),
        nullable=True,
        default="manual",
        comment="来源：manual|viral_analyzer|ai_generated",
    )
    analysis_report = Column(
        JSON,
        nullable=True,
        comment="关联的分析报告",
    )

    # 8 个核心字段
    extracted_structure = Column(
        JSON,
        nullable=False,
        default=dict,
        comment="解析结构：{hook_pattern, body_structure, cta_pattern}",
    )
    prompt_template = Column(
        Text,
        nullable=False,
        comment="Prompt 模板（含变量占位符）",
    )
    variables = Column(
        JSON,
        nullable=False,
        default=list,
        comment="变量定义：[{name, label, type, default_value}]",
    )
    engagement_benchmark = Column(
        JSON,
        default=dict,
        comment="源爆款互动数据：{likes, comments, saves, shares}",
    )
    platform_content_type_style_id = Column(
        String(64),
        ForeignKey("platform_content_type_styles.style_id", ondelete="SET NULL"),
        nullable=True,
        comment="关联 PlatformContentTypeStyle",
    )
    created_by = Column(
        String(64),
        nullable=False,
        comment="创建者：user / ai",
    )
    usage_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="使用次数",
    )
    avg_generated_engagement = Column(
        JSON,
        nullable=True,
        comment="生成内容的平均互动数据",
    )
    status = Column(
        String(32),
        default="active",
        nullable=False,
        index=True,
        comment="active | deprecated | draft",
    )

    # 关联
    platform_content_type_style = relationship(
        "PlatformContentTypeStyleORM",
        back_populates="content_templates",
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
