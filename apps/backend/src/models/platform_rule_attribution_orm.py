"""PlatformRule Attribution ORM — per-content evaluation audit trail.

Aligned with PRD V3.1 §5.6 合规审计链 (>=2年追溯).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Index, Text
from sqlalchemy.dialects.postgresql import UUID

from src.core.database import Base


class ContentRuleAttributionORM(Base):
    __tablename__ = "content_rule_attributions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id = Column(String(255), nullable=False, index=True)
    rule_id = Column(String(255), nullable=False)
    rule_name = Column(String(255), nullable=False)
    layer = Column(String(50), nullable=False)
    action = Column(String(20), nullable=False)
    matched_text = Column(Text, nullable=True)
    platform = Column(String(20), nullable=False, default="universal")
    evaluated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    tenant_id = Column(String(64), nullable=True, index=True)

    __table_args__ = (
        Index("idx_attr_content_id", "content_id", "evaluated_at"),
        Index("idx_attr_rule_id", "rule_id", "evaluated_at"),
    )
