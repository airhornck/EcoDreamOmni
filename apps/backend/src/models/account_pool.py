"""AccountPool models, in-memory store, and cookie vault (reuses W3.5 AES-256-GCM)."""

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from src.models.platform_account import _decrypt_cookie, _encrypt_cookie


@dataclass
class FingerprintProfile:
    user_agent: str
    viewport: dict  # {"width": int, "height": int}
    locale: str
    timezone: str
    canvas_noise: bool = False
    webgl_noise: bool = False


@dataclass
class ProxyConfig:
    proxy_id: str = ""  # reference to ProxyConfigEntry.id in proxy_config module
    type: str = ""
    region: str = ""


# Lifecycle-phase default daily post quotas
LIFECYCLE_QUOTAS: dict[str, int] = {
    "cold_start": 1,
    "growth": 3,
    "mature": 5,
    "dormant": 1,
}


@dataclass
class AccountPoolEntry:
    id: str
    platform: str
    account_id: str
    nickname: str
    cookie_encrypted: str
    persona: str
    content_vertical: str
    lifecycle_phase: str  # cold_start, growth, mature, dormant
    fingerprint_profile: FingerprintProfile
    proxy_config: Optional[ProxyConfig] = None
    health_score: float = 100.0
    posts_today: int = 0
    posts_week: int = 0
    posts_month: int = 0
    violation_count: int = 0
    last_login_days: int = 0
    status: str = "active"  # active, warming, blocked, expired
    anomaly_flags: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    # ── daily quota ──
    daily_quota: int = 0
    last_post_reset: str = ""  # ISO date, e.g. "2026-05-29"

    # ── engagement data recovery ──
    auto_engagement_fetch: bool = False  # 默认关闭，需运营显式开启
    engagement_fetches_today: int = 0
    last_engagement_fetch_reset: str = ""  # ISO date, e.g. "2026-05-29"

    @property
    def cookie(self) -> str:
        return _decrypt_cookie(self.cookie_encrypted)

    @cookie.setter
    def cookie(self, value: str) -> None:
        self.cookie_encrypted = _encrypt_cookie(value)

    @property
    def quota_utilization(self) -> float:
        if self.daily_quota <= 0:
            return 0.0
        return round(self.posts_today / self.daily_quota * 100, 1)

    @property
    def quota_remaining(self) -> int:
        return max(0, self.daily_quota - self.posts_today)

    @property
    def quota_exceeded(self) -> bool:
        return self.posts_today >= self.daily_quota and self.daily_quota > 0


# In-memory store (MVP phase)
_account_pool_db: Dict[str, AccountPoolEntry] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _ensure_daily_reset(entry: AccountPoolEntry) -> bool:
    """Reset posts_today if last_post_reset is not today. Returns True if reset happened."""
    today = _today_iso()
    if entry.last_post_reset != today:
        entry.posts_today = 0
        entry.last_post_reset = today
        entry.updated_at = _now()
        return True
    return False


def create_pool_entry(
    platform: str,
    account_id: str,
    nickname: str,
    cookie: str,
    persona: str,
    content_vertical: str,
    lifecycle_phase: str,
    fingerprint_profile: dict,
    proxy_config: Optional[dict] = None,
    health_score: float = 100.0,
) -> AccountPoolEntry:
    entry_id = secrets.token_urlsafe(16)
    now = _now()
    today = _today_iso()
    fp = FingerprintProfile(**fingerprint_profile) if isinstance(fingerprint_profile, dict) else fingerprint_profile
    proxy = ProxyConfig(**proxy_config) if isinstance(proxy_config, dict) else proxy_config
    quota = LIFECYCLE_QUOTAS.get(lifecycle_phase, 1)
    entry = AccountPoolEntry(
        id=entry_id,
        platform=platform,
        account_id=account_id,
        nickname=nickname,
        cookie_encrypted=_encrypt_cookie(cookie),
        persona=persona,
        content_vertical=content_vertical,
        lifecycle_phase=lifecycle_phase,
        fingerprint_profile=fp,
        proxy_config=proxy,
        health_score=health_score,
        created_at=now,
        updated_at=now,
        daily_quota=quota,
        last_post_reset=today,
    )
    _account_pool_db[entry_id] = entry
    return entry


def get_pool_entry(entry_id: str) -> Optional[AccountPoolEntry]:
    entry = _account_pool_db.get(entry_id)
    if entry:
        _ensure_daily_reset(entry)
    return entry


def list_pool_entries(lifecycle_phase: Optional[str] = None) -> List[AccountPoolEntry]:
    entries = list(_account_pool_db.values())
    for e in entries:
        _ensure_daily_reset(e)
    if lifecycle_phase:
        entries = [e for e in entries if e.lifecycle_phase == lifecycle_phase]
    return entries


def update_pool_entry(entry_id: str, **kwargs) -> Optional[AccountPoolEntry]:
    entry = _account_pool_db.get(entry_id)
    if entry is None:
        return None
    # P2 Fix: Invalidate XhsClient cache when cookie or proxy changes
    cookie_changed = "cookie" in kwargs
    proxy_changed = "proxy_config" in kwargs

    if cookie_changed:
        entry.cookie = kwargs.pop("cookie")
    if "fingerprint_profile" in kwargs:
        entry.fingerprint_profile = FingerprintProfile(**kwargs.pop("fingerprint_profile"))
    if proxy_changed:
        pc = kwargs.pop("proxy_config")
        entry.proxy_config = ProxyConfig(**pc) if pc else None
    for key, value in kwargs.items():
        if hasattr(entry, key) and key not in ("cookie", "fingerprint_profile", "proxy_config"):
            setattr(entry, key, value)
    entry.updated_at = _now()

    # Invalidate cached client so next publish uses new config
    if cookie_changed or proxy_changed:
        try:
            from src.services.xhs_publisher import invalidate_xhs_client_cache
            invalidate_xhs_client_cache(entry.cookie)
        except Exception:
            pass
    return entry


def delete_pool_entry(entry_id: str) -> bool:
    entry = _account_pool_db.get(entry_id)
    if entry is None:
        return False
    # P2 Fix: Clear cached client before deleting account
    try:
        from src.services.xhs_publisher import invalidate_xhs_client_cache
        invalidate_xhs_client_cache(entry.cookie)
    except Exception:
        pass
    del _account_pool_db[entry_id]
    return True


def clear_pool_entries() -> None:
    _account_pool_db.clear()


# ─── Persistent storage bridge (P0 Fix: account pool durability) ───

async def load_pool_from_db(db) -> int:
    """Load account pool entries from PostgreSQL into memory cache.

    Called once at application startup.
    Returns the number of entries loaded.
    """
    from sqlalchemy import select
    from src.models.account_pool_orm import AccountPoolEntryORM

    result = await db.execute(select(AccountPoolEntryORM))
    rows = result.scalars().all()
    _account_pool_db.clear()
    for row in rows:
        fp = FingerprintProfile(**row.fingerprint_profile) if row.fingerprint_profile else FingerprintProfile(user_agent="", viewport={"width": 390, "height": 844}, locale="zh-CN", timezone="Asia/Shanghai")
        proxy = ProxyConfig(**row.proxy_config) if row.proxy_config else None
        entry = AccountPoolEntry(
            id=row.id,
            platform=row.platform,
            account_id=row.account_id,
            nickname=row.nickname,
            cookie_encrypted=row.cookie_encrypted,
            persona=row.persona,
            content_vertical=row.content_vertical,
            lifecycle_phase=row.lifecycle_phase,
            fingerprint_profile=fp,
            proxy_config=proxy,
            health_score=row.health_score,
            posts_today=row.posts_today,
            posts_week=row.posts_week,
            posts_month=row.posts_month,
            violation_count=row.violation_count,
            last_login_days=row.last_login_days,
            status=row.status,
            anomaly_flags=row.anomaly_flags or [],
            created_at=row.created_at.isoformat() if row.created_at else _now(),
            updated_at=row.updated_at.isoformat() if row.updated_at else _now(),
            daily_quota=row.daily_quota,
            last_post_reset=row.last_post_reset,
            auto_engagement_fetch=row.auto_engagement_fetch,
            engagement_fetches_today=row.engagement_fetches_today,
            last_engagement_fetch_reset=row.last_engagement_fetch_reset,
        )
        _account_pool_db[entry.id] = entry
    return len(rows)


async def save_pool_entry_to_db(db, entry: AccountPoolEntry) -> None:
    """Upsert a single account pool entry to PostgreSQL."""
    from sqlalchemy import select
    from src.models.account_pool_orm import AccountPoolEntryORM

    result = await db.execute(select(AccountPoolEntryORM).where(AccountPoolEntryORM.id == entry.id))
    row = result.scalar_one_or_none()

    fp_dict = {
        "user_agent": entry.fingerprint_profile.user_agent,
        "viewport": entry.fingerprint_profile.viewport,
        "locale": entry.fingerprint_profile.locale,
        "timezone": entry.fingerprint_profile.timezone,
    }
    proxy_dict = None
    if entry.proxy_config:
        proxy_dict = {
            "proxy_id": entry.proxy_config.proxy_id,
            "type": entry.proxy_config.type,
            "region": entry.proxy_config.region,
        }

    if row is None:
        row = AccountPoolEntryORM(
            id=entry.id,
            platform=entry.platform,
            account_id=entry.account_id,
            nickname=entry.nickname,
            cookie_encrypted=entry.cookie_encrypted,
            persona=entry.persona,
            content_vertical=entry.content_vertical,
            lifecycle_phase=entry.lifecycle_phase,
            fingerprint_profile=fp_dict,
            proxy_config=proxy_dict,
            health_score=entry.health_score,
            posts_today=entry.posts_today,
            posts_week=entry.posts_week,
            posts_month=entry.posts_month,
            violation_count=entry.violation_count,
            last_login_days=entry.last_login_days,
            status=entry.status,
            anomaly_flags=entry.anomaly_flags,
            daily_quota=entry.daily_quota,
            last_post_reset=entry.last_post_reset,
            auto_engagement_fetch=entry.auto_engagement_fetch,
            engagement_fetches_today=entry.engagement_fetches_today,
            last_engagement_fetch_reset=entry.last_engagement_fetch_reset,
        )
        db.add(row)
    else:
        row.platform = entry.platform
        row.account_id = entry.account_id
        row.nickname = entry.nickname
        row.cookie_encrypted = entry.cookie_encrypted
        row.persona = entry.persona
        row.content_vertical = entry.content_vertical
        row.lifecycle_phase = entry.lifecycle_phase
        row.fingerprint_profile = fp_dict
        row.proxy_config = proxy_dict
        row.health_score = entry.health_score
        row.posts_today = entry.posts_today
        row.posts_week = entry.posts_week
        row.posts_month = entry.posts_month
        row.violation_count = entry.violation_count
        row.last_login_days = entry.last_login_days
        row.status = entry.status
        row.anomaly_flags = entry.anomaly_flags
        row.daily_quota = entry.daily_quota
        row.last_post_reset = entry.last_post_reset
        row.auto_engagement_fetch = entry.auto_engagement_fetch
        row.engagement_fetches_today = entry.engagement_fetches_today
        row.last_engagement_fetch_reset = entry.last_engagement_fetch_reset
    await db.commit()


async def delete_pool_entry_from_db(db, entry_id: str) -> None:
    """Delete an account pool entry from PostgreSQL."""
    from sqlalchemy import delete
    from src.models.account_pool_orm import AccountPoolEntryORM

    await db.execute(delete(AccountPoolEntryORM).where(AccountPoolEntryORM.id == entry_id))
    await db.commit()


async def sync_pool_to_db(db) -> int:
    """Sync all in-memory account pool entries to PostgreSQL.

    Call this periodically or before shutdown to ensure durability.
    Returns number of entries synced.
    """
    for entry in _account_pool_db.values():
        await save_pool_entry_to_db(db, entry)
    return len(_account_pool_db)
