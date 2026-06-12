"""Agent ORM model — v4.0 Agent-First Architecture.

Persistent storage for platform+format specific content generation agents.
Previously stored in-memory in agent_hub.py; v4.0 migrates to PostgreSQL.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Text, Integer, Float, DateTime, Index, JSON, func
)
from sqlalchemy.dialects.postgresql import UUID

from src.core.database import Base


class AgentORM(Base):
    """Agent 真源表 — 面向平台+格式的内容生成 Agent 注册信息."""

    __tablename__ = "agents"
    __table_args__ = (
        Index("ix_agents_status", "status"),
        Index("ix_agents_role", "role"),
        {"comment": "Agent Registry — v4.0 Agent-First"},
    )

    id = Column(String(64), primary_key=True, comment="Agent ID, e.g. content_forge_xhs_image")
    name = Column(String(128), nullable=False, comment="显示名称，如'小红书图文生成 Agent'")
    role = Column(String(64), nullable=False, comment="角色类型，如 content_generation")
    description = Column(Text, nullable=True, comment="Agent 能力描述")
    avatar_url = Column(String(512), nullable=True, comment="头像/图标 URL")

    skills = Column(JSON, default=list, comment="能力标签列表，如 ['text_generate_skill', ...]")
    supported_platforms = Column(JSON, default=list, comment="支持的平台列表，如 ['xiaohongshu']")
    supported_formats = Column(JSON, default=list, comment="支持的内容格式列表，如 ['图文']")

    config = Column(JSON, default=dict, comment="Agent 配置，含 default_workflow_template_id 等")
    success_rate = Column(Float, default=0.92, comment="最近 24h 成功率 0.0~1.0")
    recent_tasks_1h = Column(Integer, default=0, comment="最近 1h 处理任务数")

    status = Column(
        String(32),
        nullable=False,
        default="ACTIVE",
        comment="ACTIVE | DEGRADED | OFFLINE",
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
