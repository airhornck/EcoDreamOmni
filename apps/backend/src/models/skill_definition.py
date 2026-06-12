"""SkillDefinition ORM — v4.0 Phase 8 P8-5.

独立 ORM 模型，替代 skill_hub.py 中的内存 dataclass。
MVP: 基础字段与 dataclass 一致，支持持久化存储。
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, JSON, Boolean, Integer, Index
from sqlalchemy.dialects.postgresql import UUID

from src.core.database import Base


class SkillDefinitionORM(Base):
    """Skill 定义真源表 — 替代内存 dataclass，支持持久化与版本化."""

    __tablename__ = "skill_definitions"
    __table_args__ = (
        Index("ix_sd_tenant_status", "tenant_id", "status"),
        Index("ix_sd_skill_id", "skill_id", "version"),
        {"comment": "SkillDefinition — PRD v4.0 §4.2"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(64), nullable=False, index=True, default="system")

    # 核心标识
    skill_id = Column(String(128), nullable=False, index=True, comment="如 content_generate")
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(32), nullable=False, default="1.0.0")

    # 执行元数据
    level = Column(String(10), nullable=False, default="L2", comment="L1/L2/L3/L4")
    input_schema = Column(JSON, default=dict)
    output_schema = Column(JSON, default=dict)
    modality_support = Column(JSON, default=lambda: {"text": True})
    requires_llm = Column(Boolean, default=False)
    llm_model_preference = Column(String(64), default="")
    required_functions = Column(JSON, default=list)
    permissions = Column(JSON, default=dict)

    # 代码与运行时
    code_path = Column(String(500), nullable=True, comment="源码文件路径，如 src/skills/xxx.py")
    meta = Column(JSON, default=dict)
    status = Column(String(32), default="active", comment="active / deprecated / draft")

    # 效果追踪（v4.0 Phase 2 预留）
    success_rate_7d = Column(Integer, default=0, comment="近7日成功率 * 100")
    avg_latency_ms = Column(Integer, default=0)
    avg_token_cost = Column(Integer, default=0)
    human_intervention_rate = Column(Integer, default=0)

    # 审计
    created_by = Column(String(255), nullable=False, default="system")
    updated_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
