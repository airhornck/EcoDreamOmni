"""ContentDraft ORM model — persistent replacement for in-memory ContentDraft.

PRD V2.7.1 §8 / §10.3
"""

from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, JSON, Float, DateTime, Index

from src.core.database import Base


class ContentDraftORM(Base):
    """ContentDraft — 内容草稿真源表."""

    __tablename__ = "content_drafts"
    __table_args__ = (
        Index("ix_cd_account", "account_id"),
        {"comment": "ContentDraft — PRD V2.7.1 §8"},
    )

    id = Column(String(64), primary_key=True, comment="草稿ID")
    title = Column(String(255), nullable=False, comment="标题")
    content_type = Column(String(16), nullable=False, comment="类型: note | video | carousel")
    platform = Column(String(16), nullable=False, default="xhs", comment="平台")
    account_id = Column(String(64), nullable=False, index=True, comment="关联账号池ID")
    body = Column(Text(), nullable=False, default="", comment="正文")
    tags = Column(JSON, nullable=False, default=list, comment="标签列表")
    status = Column(
        String(16),
        nullable=False,
        default="draft",
        comment="draft | reviewing | approved | published | rejected",
    )
    cover_image_url = Column(String(512), nullable=True, comment="封面图URL")
    engagement_estimate = Column(Float(), nullable=True, comment="Engagement预估")
    created_by = Column(String(64), nullable=True, index=True, comment="创建者用户ID")

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
    published_at = Column(DateTime(timezone=True), nullable=True, comment="发布时间")
