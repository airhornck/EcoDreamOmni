"""PublishTask ORM model — persistent replacement for in-memory PublishTask.

PRD V2.7.1 §10.3
"""

from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, DateTime, Index

from src.core.database import Base


class PublishTaskORM(Base):
    """PublishTask — 发布任务真源表."""

    __tablename__ = "publish_tasks"
    __table_args__ = (
        Index("ix_pt_draft", "draft_id"),
        Index("ix_pt_account", "account_id"),
        Index("ix_pt_task_hub", "task_hub_task_id"),
        {"comment": "PublishTask — PRD V2.7.1 §10.3"},
    )

    id = Column(String(64), primary_key=True, comment="发布任务ID")
    draft_id = Column(String(64), nullable=False, index=True, comment="关联ContentDraftID")
    account_id = Column(String(64), nullable=False, index=True, comment="关联账号池ID")
    platform = Column(String(16), nullable=False, comment="平台")
    status = Column(
        String(16),
        nullable=False,
        default="pending",
        comment="pending | scheduled | publishing | published | failed | cancelled | skipped",
    )
    scheduled_at = Column(DateTime(timezone=True), nullable=True, comment="定时发布时间")
    published_at = Column(DateTime(timezone=True), nullable=True, comment="实际发布时间")
    published_url = Column(String(512), nullable=True, comment="发布链接")
    platform_post_id = Column(String(128), nullable=True, comment="平台帖子ID")
    error_reason = Column(String(512), nullable=True, comment="错误原因")
    publish_skipped_reason = Column(String(512), nullable=True, comment="跳过原因")
    retry_count = Column(Integer, nullable=False, default=0)
    task_hub_task_id = Column(String(64), nullable=True, index=True, comment="关联TaskHub任务ID")
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
