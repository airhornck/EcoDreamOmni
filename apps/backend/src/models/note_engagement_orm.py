"""NoteEngagement ORM model — 24h post-publish data recovery.

PRD V2.3 §2.6 / W13 DataAnalyst
Stores actual engagement metrics fetched from XHS platform API.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Integer, DateTime, Index, JSON
)

from src.core.database import Base


class NoteEngagementORM(Base):
    """笔记互动数据真源表 — 发布后24h自动抓取或手动导入."""

    __tablename__ = "note_engagements"
    __table_args__ = (
        Index("ix_ne_account", "account_id"),
        Index("ix_ne_post", "platform_post_id"),
        Index("ix_ne_fetch_status", "fetch_status"),
        {"comment": "NoteEngagement — PRD V2.3 §2.6"},
    )

    id = Column(String(64), primary_key=True, comment="互动记录ID")
    publish_task_id = Column(
        String(64),
        nullable=False,
        index=True,
        comment="关联发布任务ID (publish_tasks 或 tasks)",
    )
    account_id = Column(String(64), nullable=False, index=True, comment="关联账号池ID")
    platform_post_id = Column(String(128), nullable=False, index=True, comment="平台帖子ID (note_id)")

    # 核心互动指标
    likes = Column(Integer, nullable=True, comment="点赞数")
    comments = Column(Integer, nullable=True, comment="评论数")
    saves = Column(Integer, nullable=True, comment="收藏数")
    shares = Column(Integer, nullable=True, comment="分享数")
    views = Column(Integer, nullable=True, comment="阅读量（可能不可用）")

    # 获取状态
    fetch_status = Column(
        String(16),
        nullable=False,
        default="pending",
        comment="pending | success | failed | manual",
    )
    fetch_error = Column(String(512), nullable=True, comment="获取失败原因")
    fetched_at = Column(DateTime(timezone=True), nullable=True, comment="数据获取时间")

    # 原始响应（用于调试和字段变更追溯）
    raw_response = Column(JSON, nullable=True, comment="平台原始响应JSON")

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


