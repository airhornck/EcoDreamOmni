"""PlatformRule ORM model — W14 Foundation Function.

平台规则真源基座：小红书规则迁移 + 抖音/视频号扩展预留.
Aligned with PRD V3.1 §PlatformRule / TASK_V2.7.1 FUNC-5.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime, JSON, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID

from src.core.database import Base


class PlatformRuleORM(Base):
    """平台规则真源表 — L1-L4规则版本化管理."""

    __tablename__ = "platform_rules"
    __table_args__ = (
        Index("ix_pr_platform_layer", "platform", "layer"),
        Index("ix_pr_platform_enabled", "platform", "enabled"),
        {"comment": "PlatformRule — PRD V3.1 §PlatformRule"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 平台标识 — 支持多平台扩展
    platform = Column(
        String(20),
        nullable=False,
        default="xiaohongshu",
        comment="xiaohongshu | douyin | video_channel | weibo",
    )

    # 规则层级
    layer = Column(
        String(10),
        nullable=False,
        comment="l1_static | l2_keyword | l3_account_state | l4_dynamic_risk",
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # 规则条件 — JSON格式存储条件DSL
    condition_json = Column(
        JSON,
        nullable=False,
        comment="{type, scope, condition/pattern, case_sensitive, ...}",
    )

    # 规则动作
    action = Column(
        String(20),
        nullable=False,
        default="warn",
        comment="block | warn | suggest | flag_for_review",
    )
    priority = Column(Integer, default=0, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)

    # 版本化与生效控制
    version = Column(Integer, default=1, nullable=False)
    effective_from = Column(DateTime(timezone=True), nullable=False)
    effective_until = Column(DateTime(timezone=True), nullable=True)

    # 关联账号池 — 规则可绑定特定账号生命周期阶段
    applicable_lifecycle = Column(
        JSON,
        default=list,
        comment="适用生命周期: [cold_start, growth, mature, dormant]",
    )

    # 审计
    created_by = Column(String(100), nullable=False)
    updated_by = Column(String(100), nullable=True)
    tenant_id = Column(String(64), nullable=True, index=True)

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


class PlatformRuleHistoryORM(Base):
    """平台规则版本历史表 — 修改留痕 ≥2年."""

    __tablename__ = "platform_rule_history"
    __table_args__ = (
        Index("ix_prh_rule_version", "rule_id", "version"),
        {"comment": "PlatformRule版本历史"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id = Column(
        UUID(as_uuid=True),
        ForeignKey("platform_rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 快照字段
    platform = Column(String(20), nullable=False)
    layer = Column(String(10), nullable=False)
    name = Column(String(255), nullable=False)
    condition_json = Column(JSON, nullable=False)
    action = Column(String(20), nullable=False)
    priority = Column(Integer, nullable=False)
    enabled = Column(Boolean, nullable=False)
    version = Column(Integer, nullable=False)
    effective_from = Column(DateTime(timezone=True), nullable=False)

    # 变更记录
    change_reason = Column(Text, nullable=True)
    changed_by = Column(String(100), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
