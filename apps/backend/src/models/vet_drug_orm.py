"""VetDrugDB ORM model — W14 Foundation Function (V3.1新增).

兽药批文真源表：批文录入、宣称校验、到期预警、产品关联.
Aligned with PRD V3.1 §VetDrugDB / TASK_V2.7.1 FUNC-3.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Text, DateTime, JSON, Index
)
from sqlalchemy.dialects.postgresql import UUID

from src.core.database import Base


class VetDrugEntryORM(Base):
    """兽药批文真源表 — 100%拦截无批文宣称."""

    __tablename__ = "vet_drug_entries"
    __table_args__ = (
        Index("ix_vd_tenant_status", "tenant_id", "status"),
        Index("ix_vd_expiry", "expiry_date", "status"),
        {"comment": "VetDrugDB — PRD V3.1 §VetDrugDB"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 核心批文号 — 格式: 兽药字xxxxxxxx / 兽药临字xxxxxxxx
    approval_number = Column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="批文号 — 兽药字/兽药临字 + 9位数字",
    )

    # 产品信息
    product_name = Column(String(255), nullable=False, index=True)
    generic_name = Column(String(255), nullable=True, comment="通用名")
    english_name = Column(String(255), nullable=True)

    # 生产企业
    manufacturer = Column(String(255), nullable=True)
    manufacturer_address = Column(Text, nullable=True)

    # 成分与规格
    ingredients = Column(Text, nullable=True, comment="主要成分")
    specifications = Column(Text, nullable=True, comment="规格")

    # 适应症与用法
    indications = Column(Text, nullable=True, comment="适应症/功能主治 — 宣称校验依据")
    usage_dosage = Column(Text, nullable=True)
    contraindications = Column(Text, nullable=True)
    adverse_reactions = Column(Text, nullable=True)
    precautions = Column(Text, nullable=True)
    drug_interactions = Column(Text, nullable=True)
    storage_conditions = Column(Text, nullable=True)

    # 批文分类
    category = Column(
        String(50),
        nullable=True,
        comment="化学药品 | 中兽药 | 生物制品 | 消毒剂",
    )
    drug_type = Column(
        String(50),
        nullable=True,
        comment="处方药 | 非处方药",
    )

    # 批文时间线
    issue_date = Column(DateTime(timezone=True), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True, comment="到期日 — 提前90天预警")
    status = Column(
        String(20),
        nullable=False,
        default="ACTIVE",
        comment="ACTIVE | EXPIRED | REVOKED | SUSPENDED",
    )

    # 适用对象
    applicable_species = Column(JSON, default=list, comment="适用动物种类: [cat, dog, rabbit, ...]")
    target_diseases = Column(JSON, default=list, comment="目标疾病标签")
    tags = Column(JSON, default=list)

    # 关联BrandKnowledge产品ID
    brand_knowledge_id = Column(String(32), nullable=True, index=True)

    # 审计
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    data_source = Column(
        String(50),
        nullable=True,
        default="manual",
        comment="manual | csv_import | api_sync",
    )
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
