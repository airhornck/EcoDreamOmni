"""AccountPool ORM — persistent storage for account pool entries.

Migrates the in-memory _account_pool_db to PostgreSQL for data durability
across container restarts.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime, JSON, Index
)

from src.core.database import Base


class AccountPoolEntryORM(Base):
    """账号池持久化表 — PRD V2.7.1 §8.2."""

    __tablename__ = "account_pool_entries"
    __table_args__ = (
        Index("ix_ap_entries_platform", "platform"),
        Index("ix_ap_entries_status", "status"),
        Index("ix_ap_entries_lifecycle", "lifecycle_phase"),
        {"comment": "AccountPool — persistent account entries"},
    )

    id = Column(String(64), primary_key=True, comment="账号池条目ID")
    platform = Column(String(16), nullable=False, comment="平台: xhs | douyin | wechat_channels")
    account_id = Column(String(64), nullable=False, comment="平台账号ID")
    nickname = Column(String(128), nullable=False, comment="显示昵称")
    cookie_encrypted = Column(String(2048), nullable=False, comment="AES-256-GCM加密后的Cookie")
    persona = Column(String(64), nullable=False, comment="关联PersonaID")
    content_vertical = Column(String(64), nullable=False, comment="内容垂类")
    lifecycle_phase = Column(String(32), nullable=False, comment="生命周期: cold_start | growth | mature | dormant")

    fingerprint_profile = Column(JSON, default=dict, comment="浏览器指纹配置")
    proxy_config = Column(JSON, nullable=True, comment="代理配置 {proxy_id, type, region}")

    health_score = Column(Float, nullable=False, default=100.0, comment="健康分 0-100")
    posts_today = Column(Integer, nullable=False, default=0, comment="今日发布数")
    posts_week = Column(Integer, nullable=False, default=0, comment="本周发布数")
    posts_month = Column(Integer, nullable=False, default=0, comment="本月发布数")
    violation_count = Column(Integer, nullable=False, default=0, comment="违规次数")
    last_login_days = Column(Integer, nullable=False, default=0, comment="距上次登录天数")
    status = Column(String(32), nullable=False, default="active", comment="active | warming | blocked | expired")
    anomaly_flags = Column(JSON, default=list, comment="异常标记列表")

    daily_quota = Column(Integer, nullable=False, default=0, comment="每日配额")
    last_post_reset = Column(String(16), nullable=True, comment="上次配额重置日期 ISO")

    auto_engagement_fetch = Column(Boolean, nullable=False, default=False, comment="自动抓取互动数据")
    engagement_fetches_today = Column(Integer, nullable=False, default=0, comment="今日抓取次数")
    last_engagement_fetch_reset = Column(String(16), nullable=True, comment="上次抓取重置日期 ISO")

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
