"""AccountPool service: CRUD, fingerprint assignment, health scoring."""

from typing import List, Optional

from src.models.account_pool import (
    AccountPoolEntry,
    create_pool_entry,
    delete_pool_entry,
    get_pool_entry,
    list_pool_entries,
    update_pool_entry,
)
from src.services.fingerprint_engine import generate_fingerprint


def _normalize_platform(platform: str) -> str:
    """Normalize frontend platform_id to internal storage key."""
    return "xhs" if platform == "xiaohongshu" else platform


def create_account(
    platform: str,
    account_id: str,
    nickname: str,
    cookie: str,
    persona: str,
    content_vertical: str,
    lifecycle_phase: str,
    fingerprint_profile: Optional[dict] = None,
    proxy_config: Optional[dict] = None,
) -> AccountPoolEntry:
    """Create a new pool account. Auto-generates fingerprint if not provided."""
    fp = fingerprint_profile if fingerprint_profile else generate_fingerprint()
    return create_pool_entry(
        platform=_normalize_platform(platform),
        account_id=account_id,
        nickname=nickname,
        cookie=cookie,
        persona=persona,
        content_vertical=content_vertical,
        lifecycle_phase=lifecycle_phase,
        fingerprint_profile=fp,
        proxy_config=proxy_config,
    )


def list_accounts(lifecycle_phase: Optional[str] = None) -> List[AccountPoolEntry]:
    return list_pool_entries(lifecycle_phase)


def get_account(entry_id: str) -> Optional[AccountPoolEntry]:
    return get_pool_entry(entry_id)


def update_account(entry_id: str, **kwargs) -> Optional[AccountPoolEntry]:
    from src.models.account_pool import LIFECYCLE_QUOTAS

    # If lifecycle_phase changes, auto-update daily_quota to match
    if "lifecycle_phase" in kwargs:
        new_phase = kwargs["lifecycle_phase"]
        kwargs["daily_quota"] = LIFECYCLE_QUOTAS.get(new_phase, 1)
    return update_pool_entry(entry_id, **kwargs)


def remove_account(entry_id: str) -> bool:
    return delete_pool_entry(entry_id)
