"""TaskHub ORM model — PRD V2.7.1 §10.3.

TaskHub 任务真源表：任务全生命周期管理、状态机、人工审核、发布绑定.
与 PersonaStory / WorkflowEngine / Publisher 存在逻辑关联.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Text, Integer, DateTime, ForeignKey, Index, JSON
)
from sqlalchemy.dialects.postgresql import UUID

from src.core.database import Base


class TaskORM(Base):
    """TaskHub 任务主表 — 内容生产任务全生命周期真源."""

    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_account", "account_id"),
        Index("ix_tasks_persona", "persona_id"),
        Index("ix_tasks_template", "workflow_template_id"),
        Index("ix_tasks_parent", "parent_task_id"),
        Index("ix_tasks_tenant_status", "tenant_id", "status"),
        {"comment": "TaskHub — PRD V2.7.1 §10.3"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String(255), nullable=False, comment="任务名称")
    workflow_template_id = Column(String(64), nullable=True, comment="关联工作流模板ID (deprecated, v4.0 使用 agent_id)")
    workflow_version = Column(Integer, nullable=False, default=1, comment="工作流版本号")

    account_id = Column(String(64), nullable=False, index=True, comment="关联账号池ID")
    persona_id = Column(String(64), nullable=False, index=True, comment="关联PersonaID")
    persona_story_id = Column(String(64), nullable=True, index=True, comment="关联PersonaStory剧本ID")
    node_id = Column(String(64), nullable=True, comment="关联剧本节点ID")
    content_series_id = Column(String(64), nullable=True, comment="关联内容系列ID")

    platform = Column(
        String(16),
        nullable=False,
        default="xhs",
        comment="发布平台: xhs | douyin | wechat_channels",
    )

    content_format = Column(
        String(32),
        nullable=True,
        comment="内容格式: 图文 | 视频 | 仅文字 | 视频复刻 | 视频原创 | 长文章",
    )

    agent_id = Column(
        String(64),
        nullable=True,
        index=True,
        comment="关联 Agent ID (v4.0 Agent-First)",
    )

    agent_config_snapshot = Column(
        JSON,
        default=dict,
        comment="创建时的 Agent 配置快照",
    )

    status = Column(
        String(32),
        nullable=False,
        default="draft",
        comment="draft | configuring | queued | running | paused | human_wait | approved_waiting_publish | completed | failed | cancelled",
    )

    priority = Column(Integer, nullable=False, default=50, comment="优先级 0-100")
    current_node_index = Column(Integer, nullable=False, default=0, comment="当前执行节点索引")

    prompt_variables = Column(JSON, default=dict, comment="工作流提示变量字典")
    content_strategy = Column(JSON, nullable=True, comment="内容策略组合 (Strategy Element Architecture)")
    methodology_stage_id = Column(String(64), nullable=True, comment="关联方法论阶段ID")
    timeline_event_id = Column(UUID(as_uuid=True), nullable=True, comment="关联时间线事件ID")
    draft_id = Column(String(64), nullable=True, index=True, comment="关联ContentDraftID")
    parent_task_id = Column(String(64), nullable=True, comment="父任务ID（批量任务）")
    scheduled_at = Column(DateTime(timezone=True), nullable=True, comment="定时执行时间")

    created_by = Column(String(64), nullable=False, default="", comment="创建者")

    # 审核字段
    review_decision = Column(
        String(16),
        nullable=True,
        comment="APPROVE | REJECT | REVISE",
    )
    reviewed_at = Column(DateTime(timezone=True), nullable=True, comment="审核时间")
    reviewer = Column(String(64), nullable=True, comment="审核人")
    review_reason = Column(String(512), nullable=True, comment="审核原因/反馈")

    # 发布字段
    publish_confirmed_at = Column(DateTime(timezone=True), nullable=True, comment="发布确认时间")
    publish_confirmer = Column(String(64), nullable=True, comment="发布确认人")
    cron_job_id = Column(String(64), nullable=True, comment="关联CronHub定时任务ID")

    # 发布结果审计（P0 Fix: 验证发布真伪的唯一技术证据）
    published_url = Column(String(512), nullable=True, comment="发布后平台URL")
    platform_post_id = Column(String(128), nullable=True, comment="平台帖子ID（如小红书note_id）")
    published_at = Column(DateTime(timezone=True), nullable=True, comment="实际发布时间")
    publish_error = Column(Text, nullable=True, comment="发布失败错误信息")

    # 执行追踪
    trace_id = Column(String(32), nullable=True, comment="OpenTelemetry Trace ID")
    execution_id = Column(String(64), nullable=True, comment="关联WorkflowEngine执行实例ID")

    # 租户隔离
    tenant_id = Column(String(64), nullable=True, index=True, comment="租户ID")

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
    completed_at = Column(DateTime(timezone=True), nullable=True, comment="完成/失败/取消时间")
