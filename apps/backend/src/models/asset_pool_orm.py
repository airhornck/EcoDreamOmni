"""AssetPool ORM model — W14 Foundation Function.

Migrates in-memory Asset dataclass to PostgreSQL/SQLAlchemy.
Aligned with PRD V3.1 §AssetPool / TASK_V2.7.1 FUNC-1.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime, JSON, Index
)
from sqlalchemy.dialects.postgresql import UUID

from src.core.database import Base


class AssetORM(Base):
    """素材库真源表 — 三源混合（运营上传/STOCK_API/AI生成）."""

    __tablename__ = "assets"
    __table_args__ = (
        Index("ix_assets_tenant_status", "tenant_id", "status"),
        Index("ix_assets_source_category", "source_type", "category"),
        {"comment": "AssetPool — PRD V3.1 §AssetPool"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    file_url = Column(Text, nullable=False)
    thumbnail_url = Column(Text, nullable=True)

    # 三源类型
    source_type = Column(
        String(20),
        nullable=False,
        default="OPERATOR_UPLOAD",
        comment="OPERATOR_UPLOAD | STOCK_API | AI_GENERATED",
    )
    license_type = Column(
        String(20),
        nullable=False,
        default="OWNED",
        comment="OWNED | LICENSED | AI_GENERATED",
    )
    license_status = Column(
        String(20),
        nullable=False,
        default="VALID",
        comment="VALID | EXPIRING_SOON | EXPIRED",
    )

    # 版权信息
    copyright_holder = Column(String(255), nullable=True)
    copyright_year = Column(Integer, nullable=True)
    usage_rights = Column(JSON, default=list)
    copyright_validated = Column(Boolean, default=False, nullable=False)
    license_ref = Column(Text, nullable=True, comment="License agreement text or URL")

    # 图库API特有
    stock_source = Column(String(50), nullable=True, comment="shutterstock, getty, etc.")
    stock_id = Column(String(100), nullable=True)
    license_expiry = Column(DateTime(timezone=True), nullable=True)

    # AI生成特有
    ai_model = Column(String(100), nullable=True)
    ai_prompt = Column(Text, nullable=True)
    ai_disclosure = Column(Boolean, default=False, nullable=False)
    ai_metadata = Column(JSON, nullable=True, comment="Generation params dict")

    # 分类标签
    category = Column(String(50), nullable=True, comment="cat | dog | general_pet | brand_material | product | scene")
    tags = Column(JSON, default=list)
    description = Column(Text, nullable=True)

    # 系列关联
    series_id = Column(String(32), nullable=True, index=True)

    # 关联外部真源
    brand_knowledge_id = Column(String(32), nullable=True, index=True, comment="关联BrandKnowledge产品ID")

    # 状态
    status = Column(
        String(20),
        nullable=False,
        default="ACTIVE",
        comment="ACTIVE | PENDING_REVIEW | DELETED | EXPIRED",
    )

    # 元数据（扁平化存储避免JSON嵌套查询性能问题）
    meta_width = Column(Integer, nullable=True)
    meta_height = Column(Integer, nullable=True)
    meta_file_size = Column(Integer, nullable=True)
    meta_mime_type = Column(String(50), nullable=True)
    meta_dominant_color = Column(String(20), nullable=True)

    # 上传者 / 租户隔离
    uploaded_by = Column(String(100), nullable=True)
    tenant_id = Column(String(64), nullable=True, index=True)

    # 审计时间戳
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
