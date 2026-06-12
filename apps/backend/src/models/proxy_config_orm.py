"""Proxy configuration ORM — persistent storage for proxy entries.

Migrates the in-memory _proxy_db to PostgreSQL for data durability
across container restarts.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Index
)

from src.core.database import Base


class ProxyConfigORM(Base):
    """代理配置持久化表 — 支持容器重启后自动恢复."""

    __tablename__ = "proxy_configs"
    __table_args__ = (
        Index("ix_proxy_configs_protocol", "protocol"),
        Index("ix_proxy_configs_is_active", "is_active"),
        {"comment": "ProxyConfig — persistent proxy entries"},
    )

    id = Column(String(64), primary_key=True, comment="代理条目ID")
    name = Column(String(128), nullable=False, comment="显示名称")
    provider = Column(String(64), nullable=False, default="custom", comment="供应商: brightdata | oxylabs | custom")
    protocol = Column(String(16), nullable=False, default="http", comment="协议: http | https | socks5")
    host = Column(String(256), nullable=False, comment="代理主机地址")
    port = Column(Integer, nullable=False, comment="代理端口")
    username = Column(String(256), nullable=False, default="", comment="认证用户名")
    password = Column(String(256), nullable=False, default="", comment="认证密码")
    region = Column(String(64), nullable=False, default="", comment="区域")
    rotation_type = Column(String(32), nullable=False, default="static", comment="轮换类型: static | session | rotating")
    is_active = Column(Boolean, nullable=False, default=True, comment="是否激活")
    health_status = Column(String(32), nullable=False, default="unknown", comment="健康状态: healthy | unhealthy | unknown")
    last_check_at = Column(DateTime(timezone=True), nullable=True, comment="最后检查时间")
    fail_count = Column(Integer, nullable=False, default=0, comment="连续失败次数")
    success_count = Column(Integer, nullable=False, default=0, comment="成功次数")

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
