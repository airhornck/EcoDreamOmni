"""Copilot-Driven ORM models — v4.0 Step 2 契约冻结.

Tables:
  - copilot_context_sessions: Copilot 上下文会话（TTL 30min）
  - ai_cover_generation_jobs: AI 封面生成异步任务
  - copilot_action_logs: Copilot 操作审计日志（保留 90 天）
"""

import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import (
    Column, String, Text, Integer, DateTime, Boolean, JSON, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID

from src.core.database import Base


class CopilotContextSessionORM(Base):
    """Copilot 上下文会话表 — 驱动 Action Cards 的动态组装."""

    __tablename__ = "copilot_context_sessions"
    __table_args__ = (
        Index("ix_copilot_sessions_user", "user_id", "updated_at"),
        Index("ix_copilot_sessions_expires", "expires_at"),
        UniqueConstraint("session_id", name="uq_copilot_session_id"),
        {"comment": "Copilot 上下文会话 — TTL 30min"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(64), nullable=False, index=True, comment="用户ID")
    session_id = Column(String(64), nullable=False, unique=True, comment="客户端会话ID")
    page = Column(String(64), nullable=False, comment="当前页面路由")
    selected_items = Column(JSON, default=list, comment="选中项ID列表")
    selected_content = Column(JSON, default=dict, comment="选中内容摘要")
    workspace_state = Column(JSON, default=dict, comment="工作区状态")
    suggested_cards = Column(JSON, default=list, comment="后端预计算的卡片建议")
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
    expires_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc) + timedelta(minutes=30),
        nullable=False,
        comment="过期时间，默认 NOW() + 30min",
    )


class AICoverGenerationJobORM(Base):
    """AI 封面生成异步任务表."""

    __tablename__ = "ai_cover_generation_jobs"
    __table_args__ = (
        Index("idx_cover_jobs_user_created", "user_id", "created_at"),
        Index("idx_cover_jobs_task", "task_id"),
        {"comment": "AI 封面生成异步任务"},
    )

    id = Column(String(32), primary_key=True, comment="任务ID，如 cover_gen_xyz789")
    task_id = Column(String(32), nullable=False, comment="关联 tasks.id")
    user_id = Column(String(32), nullable=False, comment="用户ID")
    prompt = Column(Text, nullable=True, comment="用户输入的提示词")
    auto_prompt = Column(Boolean, default=False, comment="是否自动根据内容生成提示词")
    style_preset = Column(String(32), nullable=True, comment="风格预设")
    count = Column(Integer, default=2, comment="生成数量")
    ratio = Column(String(10), default="3:4", comment="裁剪比例")
    status = Column(
        String(20),
        default="queued",
        comment="queued | generating | completed | failed",
    )
    results = Column(JSON, default=list, comment="生成结果 [{url, thumbnail_url, ratio, seed}]")
    error_message = Column(Text, nullable=True, comment="失败原因")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at = Column(DateTime(timezone=True), nullable=True, comment="完成时间")


class CopilotActionLogORM(Base):
    """Copilot 操作审计日志表 — 保留 90 天."""

    __tablename__ = "copilot_action_logs"
    __table_args__ = (
        Index("idx_copilot_logs_user", "user_id", "created_at"),
        Index("idx_copilot_logs_session", "session_id"),
        {"comment": "Copilot 操作审计日志 — 保留 90 天"},
    )

    id = Column(String(32), primary_key=True, comment="日志ID")
    user_id = Column(String(32), nullable=False, comment="用户ID")
    session_id = Column(String(64), nullable=False, comment="会话ID")
    context_id = Column(String(32), nullable=True, comment="上下文ID")
    card_id = Column(String(64), nullable=True, comment="Action Card ID")
    action_id = Column(String(64), nullable=True, comment="执行的 Action ID")
    page = Column(String(64), nullable=True, comment="所在页面")
    status = Column(
        String(20),
        nullable=True,
        comment="success | failed | cancelled",
    )
    request_payload = Column(JSON, default=dict, comment="请求体")
    response_payload = Column(JSON, default=dict, comment="响应体")
    execution_time_ms = Column(Integer, nullable=True, comment="执行耗时(ms)")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
