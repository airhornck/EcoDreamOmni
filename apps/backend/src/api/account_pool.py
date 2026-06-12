"""AccountPool API routes: CRUD, fingerprint, health, browser context."""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.dependencies import get_current_user
from src.models.user import User
from src.services.account_pool_service import (
    create_account,
    get_account,
    list_accounts,
    remove_account,
    update_account,
)
from src.services.browser_pool import BrowserPool, build_context_config

router = APIRouter(prefix="/account-pool", tags=["account-pool"])


# ─── Request/Response Models ───


class FingerprintProfileInput(BaseModel):
    user_agent: str
    viewport: dict
    locale: str
    timezone: str
    canvas_noise: bool = False
    webgl_noise: bool = False


class ProxyConfigInput(BaseModel):
    proxy_id: str = ""
    type: str = ""
    region: str = ""


def _normalize_platform(platform: str) -> str:
    """Normalize frontend platform_id to internal storage key."""
    return "xhs" if platform == "xiaohongshu" else platform


class CreateAccountPoolRequest(BaseModel):
    platform: str = Field(..., description="Platform type: xiaohongshu, douyin, wechat_channels")
    account_id: str
    nickname: str
    cookie: str
    persona: str
    content_vertical: str
    lifecycle_phase: str = Field(default="cold_start", description="cold_start, growth, mature, dormant")
    fingerprint_profile: Optional[FingerprintProfileInput] = None
    proxy_config: Optional[ProxyConfigInput] = None


class UpdateAccountPoolRequest(BaseModel):
    nickname: Optional[str] = None
    cookie: Optional[str] = None
    persona: Optional[str] = None
    content_vertical: Optional[str] = None
    lifecycle_phase: Optional[str] = None
    fingerprint_profile: Optional[FingerprintProfileInput] = None
    proxy_config: Optional[ProxyConfigInput] = None
    health_score: Optional[float] = None
    status: Optional[str] = None
    daily_quota: Optional[int] = None
    auto_engagement_fetch: Optional[bool] = None


class FingerprintProfileResponse(BaseModel):
    user_agent: str
    viewport: dict
    locale: str
    timezone: str
    canvas_noise: bool
    webgl_noise: bool


class ProxyConfigResponse(BaseModel):
    proxy_id: str
    type: str
    region: str


class AccountPoolResponse(BaseModel):
    id: str
    platform: str
    account_id: str
    nickname: str
    persona: str
    content_vertical: str
    lifecycle_phase: str
    fingerprint_profile: FingerprintProfileResponse
    proxy_config: Optional[ProxyConfigResponse] = None
    health_score: float
    posts_today: int
    posts_week: int
    posts_month: int
    violation_count: int
    last_login_days: int
    status: str
    anomaly_flags: List[str]
    created_at: str
    updated_at: str
    # 配额字段
    daily_quota: int = 0
    last_post_reset: str = ""
    quota_utilization: float = 0.0
    quota_remaining: int = 0
    quota_exceeded: bool = False
    # 数据回收开关
    auto_engagement_fetch: bool = False
    # 前端兼容字段
    username: str = ""
    persona_name: str = ""


class AccountPoolListResponse(BaseModel):
    accounts: List[AccountPoolResponse]
    total: int
    stats: dict = {}


class BrowserContextConfigResponse(BaseModel):
    config: dict


# ─── Helpers ───


def _fp_to_response(fp) -> FingerprintProfileResponse:
    return FingerprintProfileResponse(
        user_agent=fp.user_agent,
        viewport=fp.viewport,
        locale=fp.locale,
        timezone=fp.timezone,
        canvas_noise=fp.canvas_noise,
        webgl_noise=fp.webgl_noise,
    )


def _proxy_to_response(px) -> Optional[ProxyConfigResponse]:
    if px is None:
        return None
    return ProxyConfigResponse(proxy_id=px.proxy_id, type=px.type, region=px.region)


def _to_response(entry) -> AccountPoolResponse:
    return AccountPoolResponse(
        id=entry.id,
        platform="xiaohongshu" if entry.platform == "xhs" else entry.platform,
        account_id=entry.account_id,
        nickname=entry.nickname,
        persona=entry.persona,
        content_vertical=entry.content_vertical,
        lifecycle_phase=entry.lifecycle_phase,
        fingerprint_profile=_fp_to_response(entry.fingerprint_profile),
        proxy_config=_proxy_to_response(entry.proxy_config),
        health_score=entry.health_score,
        posts_today=entry.posts_today,
        posts_week=entry.posts_week,
        posts_month=entry.posts_month,
        violation_count=entry.violation_count,
        last_login_days=entry.last_login_days,
        status=entry.status,
        anomaly_flags=entry.anomaly_flags,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        # 配额字段
        daily_quota=entry.daily_quota,
        last_post_reset=entry.last_post_reset,
        quota_utilization=entry.quota_utilization,
        quota_remaining=entry.quota_remaining,
        quota_exceeded=entry.quota_exceeded,
        auto_engagement_fetch=entry.auto_engagement_fetch,
        # 前端兼容字段
        username=entry.account_id,
        persona_name=entry.persona,
    )


# ─── Routes ───


@router.post("", status_code=status.HTTP_201_CREATED, response_model=AccountPoolResponse)
async def create_pool_account(
    req: CreateAccountPoolRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    fp = req.fingerprint_profile.model_dump() if req.fingerprint_profile else None
    proxy = req.proxy_config.model_dump() if req.proxy_config else None
    entry = create_account(
        platform=_normalize_platform(req.platform),
        account_id=req.account_id,
        nickname=req.nickname,
        cookie=req.cookie,
        persona=req.persona,
        content_vertical=req.content_vertical,
        lifecycle_phase=req.lifecycle_phase,
        fingerprint_profile=fp,
        proxy_config=proxy,
    )
    # P0 Fix: Persist to DB immediately
    from src.models.account_pool import save_pool_entry_to_db
    await save_pool_entry_to_db(db, entry)
    return _to_response(entry)


@router.get("", response_model=AccountPoolListResponse)
def list_pool_accounts(
    lifecycle_phase: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
):
    accounts = list_accounts(lifecycle_phase)
    total = len(accounts)
    active = sum(1 for a in accounts if a.status == "active")
    avg_health = sum(a.health_score for a in accounts) / total if total else 0
    today_posts = sum(a.posts_today for a in accounts)
    total_quota = sum(a.daily_quota for a in accounts)
    quota_util_avg = (
        sum(a.quota_utilization for a in accounts) / total if total else 0
    )
    return AccountPoolListResponse(
        accounts=[_to_response(a) for a in accounts],
        total=total,
        stats={
            "total": total,
            "active": active,
            "avg_health_score": round(avg_health, 1),
            "today_posts": today_posts,
            "total_quota": total_quota,
            "quota_utilization_avg": round(quota_util_avg, 1),
            "quota_exceeded_count": sum(1 for a in accounts if a.quota_exceeded),
        },
    )


@router.get("/{entry_id}", response_model=AccountPoolResponse)
def get_pool_account_detail(
    entry_id: str,
    user: User = Depends(get_current_user),
):
    entry = get_account(entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return _to_response(entry)


@router.patch("/{entry_id}", response_model=AccountPoolResponse)
async def update_pool_account(
    entry_id: str,
    req: UpdateAccountPoolRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    kwargs = req.model_dump(exclude_unset=True)
    if "fingerprint_profile" in kwargs and kwargs["fingerprint_profile"] is not None:
        kwargs["fingerprint_profile"] = kwargs["fingerprint_profile"]
    if "proxy_config" in kwargs and kwargs["proxy_config"] is not None:
        kwargs["proxy_config"] = kwargs["proxy_config"]
    entry = update_account(entry_id, **kwargs)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    # P0 Fix: Persist to DB immediately
    from src.models.account_pool import save_pool_entry_to_db
    await save_pool_entry_to_db(db, entry)
    return _to_response(entry)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pool_account(
    entry_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    removed = remove_account(entry_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    # P0 Fix: Delete from DB
    from src.models.account_pool import delete_pool_entry_from_db
    await delete_pool_entry_from_db(db, entry_id)
    return None


@router.get("/{entry_id}/browser-config", response_model=BrowserContextConfigResponse)
def get_browser_context_config(
    entry_id: str,
    user: User = Depends(get_current_user),
):
    entry = get_account(entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    proxy_dict = None
    if entry.proxy_config and entry.proxy_config.proxy_id:
        from src.services import proxy_service as ps
        proxy_entry = ps.get_proxy(entry.proxy_config.proxy_id)
        if proxy_entry:
            proxy_dict = {
                "protocol": proxy_entry.protocol,
                "host": proxy_entry.host,
                "port": proxy_entry.port,
                "username": proxy_entry.username,
                "password": proxy_entry.password,
            }
    config = build_context_config(
        {
            "user_agent": entry.fingerprint_profile.user_agent,
            "viewport": entry.fingerprint_profile.viewport,
            "locale": entry.fingerprint_profile.locale,
            "timezone": entry.fingerprint_profile.timezone,
            "canvas_noise": entry.fingerprint_profile.canvas_noise,
            "webgl_noise": entry.fingerprint_profile.webgl_noise,
        },
        proxy_dict,
    )
    return BrowserContextConfigResponse(config=config)


# ─── Status & Persona Endpoints ───


class AccountStatusUpdateRequest(BaseModel):
    status: str


class AccountPersonaUpdateRequest(BaseModel):
    persona_id: str


@router.patch("/{entry_id}/status", response_model=AccountPoolResponse)
async def update_account_status(
    entry_id: str,
    req: AccountStatusUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新账号状态."""
    entry = update_account(entry_id, status=req.status)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    from src.models.account_pool import save_pool_entry_to_db
    await save_pool_entry_to_db(db, entry)
    return _to_response(entry)


@router.patch("/{entry_id}/persona", response_model=AccountPoolResponse)
async def update_account_persona(
    entry_id: str,
    req: AccountPersonaUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """绑定Persona."""
    entry = update_account(entry_id, persona=req.persona_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    from src.models.account_pool import save_pool_entry_to_db
    await save_pool_entry_to_db(db, entry)
    return _to_response(entry)


# ─── Daily Quota Operations ───


@router.post("/{entry_id}/consume-quota", response_model=AccountPoolResponse)
async def consume_account_quota(
    entry_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Consume one daily post quota for an account (called by publisher)."""
    from src.models.account_pool import _ensure_daily_reset

    entry = get_account(entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    _ensure_daily_reset(entry)
    if entry.quota_exceeded:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily quota exceeded ({entry.posts_today}/{entry.daily_quota})",
        )
    entry.posts_today += 1
    entry.updated_at = datetime.now(timezone.utc).isoformat()
    # P0 Fix: Persist quota change to DB
    from src.models.account_pool import save_pool_entry_to_db
    await save_pool_entry_to_db(db, entry)
    return _to_response(entry)


@router.post("/{entry_id}/reset-quota", response_model=AccountPoolResponse)
async def reset_account_quota(
    entry_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually reset daily quota counter (admin/debug)."""
    entry = update_account(entry_id, posts_today=0)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    from src.models.account_pool import save_pool_entry_to_db
    await save_pool_entry_to_db(db, entry)
    return _to_response(entry)
