"""SQLAlchemy 2.0 ORM model for users aligned with detailed design §3.1, §4.1.

Phase 3+: This replaces the in-memory User dataclass.
Current: Co-exists with in-memory store during W11–W14 migration.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID

from src.core.database import Base


class UserORM(Base):
    __tablename__ = "users"
    __table_args__ = {"comment": "Identity group — detailed design §4.1"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="operator", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    mfa_secret = Column(String(255), nullable=True)
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    tenant_id = Column(String(64), nullable=True, index=True, comment="Nullable default tenant for Phase 3")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
