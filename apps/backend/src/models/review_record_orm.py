"""ReviewRecord ORM model — persistent replacement for in-memory _review_db.

PRD V2.7.1 §10.3
"""

from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Boolean, JSON, DateTime, Index

from src.core.database import Base


class ReviewRecordORM(Base):
    """ReviewRecord — 人工审核记录真源表."""

    __tablename__ = "review_records"
    __table_args__ = (
        Index("ix_rr_task", "task_id"),
        {"comment": "ReviewRecord — PRD V2.7.1 §10.3"},
    )

    id = Column(String(64), primary_key=True, comment="审核记录ID")
    task_id = Column(String(64), nullable=False, index=True, comment="关联TaskHub任务ID")
    reviewer = Column(String(64), nullable=False, comment="审核人")
    decision = Column(
        String(16),
        nullable=False,
        comment="APPROVE | REJECT | REVISE",
    )
    reason = Column(String(512), nullable=True, comment="审核原因")
    target_node_index = Column(Integer, nullable=True, comment="目标节点索引")
    revised_variables = Column(JSON, nullable=True, comment="修订变量")
    publish_mode = Column(String(16), nullable=True, comment="immediate | scheduled")
    scheduled_at = Column(DateTime(timezone=True), nullable=True, comment="定时发布时间")
    is_dual_approval = Column(Boolean, nullable=False, default=False)
    dual_approver = Column(String(64), nullable=True, comment="二次审核人")
    task_created_by = Column(String(64), nullable=True, index=True, comment="被审核任务的创建者用户ID")

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
