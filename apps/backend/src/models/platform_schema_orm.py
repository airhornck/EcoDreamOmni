"""PlatformSchema ORM model — 平台 API 发布格式规范真源.

从 D:\project\lumina\data\platforms\*.yml 解析各平台对通过 API 发布的文章
所要求的格式结构与各字段的约束要求.

Aligned with PRD V3.1 §PlatformSchema.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime, JSON, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.core.database import Base


class PlatformSchemaORM(Base):
    """平台格式规范真源表 — 从 YAML 解析的平台 API 字段约束."""

    __tablename__ = "platform_schemas"
    __table_args__ = (
        Index("ix_ps_platform_id", "platform_id"),
        {"comment": "PlatformSchema — 平台 API 发布格式规范真源"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 平台标识 — 如 xiaohongshu, douyin, wechat_official, bilibili
    platform_id = Column(
        String(32),
        nullable=False,
        unique=True,
        index=True,
        comment="平台标识: xiaohongshu | douyin | wechat_official | bilibili",
    )

    # 平台显示名称
    display_name = Column(String(100), nullable=False)

    # 规范版本
    version = Column(String(20), nullable=False, default="v2024")

    # 内容 DNA — 平台内容风格/结构要求
    content_dna = Column(
        JSON,
        default=list,
        comment="[{element, value, validation_skill}]",
    )

    # 审核规则 — 违禁词等
    audit_rules = Column(
        JSON,
        default=list,
        comment="[{category, forbidden_terms, audit_skill, examples, notes}]",
    )

    # 关联内容格式
    content_formats = relationship(
        "PlatformContentFormatORM",
        back_populates="schema",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # 审计
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


class PlatformContentFormatORM(Base):
    """平台内容格式表 — 图文/视频/仅文字等格式定义."""

    __tablename__ = "platform_content_formats"
    __table_args__ = (
        Index("ix_pcf_schema_format", "schema_id", "format_name"),
        {"comment": "PlatformContentFormat — 平台内容格式字段约束"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 关联平台规范
    schema_id = Column(
        UUID(as_uuid=True),
        ForeignKey("platform_schemas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 格式名称 — 如 图文, 视频, 仅文字, 短视频, 图文消息
    format_name = Column(String(50), nullable=False)

    # 字段约束列表 — 统一结构化存储
    fields = Column(
        JSON,
        nullable=False,
        default=list,
        comment="[{name, label, type, required, min, max, default, description, ...}]",
    )

    # 关联
    schema = relationship("PlatformSchemaORM", back_populates="content_formats")

    # 审计
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
