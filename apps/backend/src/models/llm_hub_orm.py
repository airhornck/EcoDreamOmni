"""LLM Hub ORM models — PRD V2.7.2 §8 精简版.

厂家选择 + 模型名 + APIKey + 应用范围（全局/节点覆盖）
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    CheckConstraint,
    Index,
    Numeric,
    text,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID

from src.core.database import Base


class LLMModelORM(Base):
    __tablename__ = "llm_models"
    __table_args__ = {"comment": "LLM Hub — 模型注册表（精简版）"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(String(64), nullable=False)
    model_name = Column(String(128), nullable=False)
    api_key_encrypted = Column(Text, nullable=False)
    endpoint_base_url = Column(String(512), nullable=True)
    status = Column(String(16), default="active", nullable=False)
    data_training_opt_out = Column(Boolean, default=True, nullable=False)
    # v4.0 Phase 1 P1-4: 模态支持字段
    modality_support = Column(
        JSON,
        default=dict,
        nullable=True,
        comment="模态支持：{text: bool, image: bool, video: bool, audio: bool, embedding: bool}",
    )
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class LLMScopeConfigORM(Base):
    __tablename__ = "llm_scope_configs"
    __table_args__ = (
        CheckConstraint("scope_type IN ('global', 'node')", name="ck_scope_type"),
        CheckConstraint(
            "(scope_type = 'global' AND node_id IS NULL) OR (scope_type = 'node' AND node_id IS NOT NULL)",
            name="ck_scope_node_id",
        ),
        Index(
            "uq_global_scope",
            "scope_type",
            unique=True,
            postgresql_where=text("scope_type = 'global'"),
        ),
        Index(
            "uq_node_scope",
            "node_id",
            unique=True,
            postgresql_where=text("scope_type = 'node'"),
        ),
        {"comment": "LLM Scope Config — global default or node override"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scope_type = Column(String(16), nullable=False)
    node_id = Column(String(64), nullable=True)
    model_id = Column(
        UUID(as_uuid=True),
        ForeignKey("llm_models.id", ondelete="CASCADE"),
        nullable=False,
    )
    temperature = Column(Float, default=0.5, nullable=False)
    timeout_seconds = Column(Integer, default=60, nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class LLMUsageLogORM(Base):
    __tablename__ = "llm_usage_logs"
    __table_args__ = {"comment": "LLM 调用日志 — 成本看板数据源"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(
        UUID(as_uuid=True),
        ForeignKey("llm_models.id", ondelete="SET NULL"),
        nullable=True,
    )
    node_id = Column(String(64), nullable=False)
    provider_region = Column(String(16), nullable=False)
    input_tokens = Column(Integer, default=0, nullable=False)
    output_tokens = Column(Integer, default=0, nullable=False)
    latency_ms = Column(Integer, default=0, nullable=False)
    status = Column(String(16), nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class LLMPricingORM(Base):
    __tablename__ = "llm_pricing"
    __table_args__ = {"comment": "LLM 定价参考表（硬编码初始化）"}

    model_name = Column(String(128), primary_key=True)
    provider = Column(String(64), nullable=False)
    input_price_per_1k = Column(Numeric(10, 6), nullable=False)
    output_price_per_1k = Column(Numeric(10, 6), nullable=False)
    currency = Column(String(8), default="CNY", nullable=False)
