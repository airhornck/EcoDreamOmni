"""Checkpoint ORM — v4.0 Phase 4 P4-3.

Pipeline 节点级状态快照持久化表。
对齐契约：docs/契约与数据/02-数据库ER图.md §2.2
"""

from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Integer, Boolean, Index, JSON

from src.core.database import Base


class CheckpointORM(Base):
    """Checkpoint — 节点级状态快照."""

    __tablename__ = "checkpoints"
    __table_args__ = (
        Index("ix_ck_execution", "execution_id"),
        Index("ix_ck_execution_node", "execution_id", "node_id"),
        {"comment": "Checkpoint — PRD v4.0 P4-3"},
    )

    checkpoint_id = Column(
        String(64), primary_key=True, comment="快照唯一标识（cp_xxx）"
    )
    execution_id = Column(
        String(64), nullable=False, index=True, comment="关联 Pipeline 执行 ID"
    )
    node_id = Column(
        String(64), nullable=False, comment="节点 ID（node_index 字符串化）"
    )
    node_status = Column(
        String(32), nullable=False, comment="SUCCESS | FAILED | SKIPPED"
    )
    input_ref = Column(
        String(256), nullable=True, comment="输入数据 S3/本地文件引用"
    )
    output_ref = Column(
        String(256), nullable=True, comment="输出数据 S3/本地文件引用"
    )
    output_summary = Column(
        String(512), nullable=True, comment="输出摘要（AI Copilot 展示用）"
    )
    started_at = Column(DateTime(timezone=True), nullable=True, comment="开始时间")
    completed_at = Column(DateTime(timezone=True), nullable=True, comment="完成时间")
    latency_ms = Column(Integer, nullable=True, comment="执行延迟（毫秒）")
    token_usage = Column(JSON, nullable=True, comment="Token 消耗：{prompt_tokens, completion_tokens}")
    is_recoverable = Column(
        Boolean, nullable=False, default=True, comment="是否可恢复"
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
