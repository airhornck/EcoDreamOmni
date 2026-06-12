"""ProhibitedWord ORM — Independent word library for compliance.

Aligned with PRD V3.1 §Compliance / 法务合规评审报告.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID

from src.core.database import Base


class ProhibitedWordORM(Base):
    __tablename__ = "prohibited_words"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    word = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False, default="general")
    severity = Column(String(10), nullable=False, default="L2")
    platform = Column(String(20), nullable=False, default="universal")
    match_type = Column(String(20), nullable=False, default="exact")
    is_enabled = Column(Boolean, default=True)
    description = Column(String(500), nullable=True)
    tenant_id = Column(String(64), nullable=True)
    created_by = Column(String(255), nullable=False, default="system")
    updated_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_prohibited_word_platform", "platform", "is_enabled"),
        Index("idx_prohibited_word_tenant", "tenant_id", "is_enabled"),
        Index("idx_prohibited_word_category", "category", "is_enabled"),
    )


class ContentGuidelineORM(Base):
    __tablename__ = "content_guidelines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(String(1000), nullable=True)
    rules_json = Column(String(2000), nullable=False, default="{}")
    platform = Column(String(20), nullable=False, default="universal")
    is_enabled = Column(Boolean, default=True)
    tenant_id = Column(String(64), nullable=True)
    created_by = Column(String(255), nullable=False, default="system")
    updated_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_guideline_platform", "platform", "is_enabled"),
        Index("idx_guideline_category", "category", "is_enabled"),
    )
