"""BrandKnowledge ORM model — W14 Foundation Function.

Knowledge base with versioning and vector search support.
Aligned with PRD V3.1 §BrandKnowledge / TASK_V2.7.1 FUNC-2.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime, JSON, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID

from pgvector.sqlalchemy import Vector

from src.core.database import Base


class BrandKnowledgeEntryORM(Base):
    """品牌知识条目真源表 — 支持版本化管理与RAG检索."""

    __tablename__ = "brand_knowledge_entries"
    __table_args__ = (
        Index("ix_bk_tenant_type", "tenant_id", "entry_type"),
        Index("ix_bk_brand_latest", "brand_name", "is_latest"),
        {"comment": "BrandKnowledge — PRD V3.1 §BrandKnowledge"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 条目类型
    entry_type = Column(
        String(50),
        nullable=False,
        comment="brand_info | category_knowledge | product_sku | faq | prohibited_claim",
    )
    name = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)

    # 产品SKU特有字段
    product_id = Column(String(32), nullable=True, index=True)
    approval_number = Column(String(50), nullable=True, index=True, comment="兽药批文号 — 强制关联VetDrugDB")
    sku_code = Column(String(100), nullable=True)
    brand_name = Column(String(100), nullable=True, index=True)

    # 合规字段
    prohibited_claims = Column(JSON, default=list, comment="禁用宣称列表")
    required_disclaimers = Column(JSON, default=list, comment="必须包含的免责声明")

    # RAG向量 — pgvector 1536维 (OpenAI/text-embedding-3-small)
    embedding = Column(Vector(1536), nullable=True)

    # 版本化
    version = Column(Integer, default=1, nullable=False)
    is_latest = Column(Boolean, default=True, nullable=False)
    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("brand_knowledge_entries.id", ondelete="SET NULL"),
        nullable=True,
        comment="上一版本ID",
    )

    # 素材关联（AssetPool外键列表，JSON存储多对多简化）
    asset_ids = Column(JSON, default=list, comment="关联AssetPool素材UUID列表")

    # 审计
    created_by = Column(String(100), nullable=False)
    updated_by = Column(String(100), nullable=True)
    change_reason = Column(Text, nullable=True, comment="修改原因 — 双人复核留痕")
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
