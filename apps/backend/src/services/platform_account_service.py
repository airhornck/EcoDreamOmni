"""Platform account service: CRUD, cookie vault, session checks."""

from typing import List, Optional

from src.models.platform_account import (
    PlatformAccount,
    create_platform_account,
    delete_platform_account,
    get_platform_account,
    list_platform_accounts,
    poll_qr_login,
    start_qr_login,
    update_platform_account,
)


def create_account(
    platform: str,
    account_id: str,
    nickname: str,
    cookie: str,
    status: str = "active",
) -> PlatformAccount:
    return create_platform_account(
        platform=platform,
        account_id=account_id,
        nickname=nickname,
        cookie=cookie,
        status=status,
    )


def list_accounts() -> List[PlatformAccount]:
    return list_platform_accounts()


def get_account(pa_id: str) -> Optional[PlatformAccount]:
    return get_platform_account(pa_id)


def update_account(pa_id: str, **kwargs) -> Optional[PlatformAccount]:
    return update_platform_account(pa_id, **kwargs)


def remove_account(pa_id: str) -> bool:
    return delete_platform_account(pa_id)


def check_session_status(pa_id: str) -> dict:
    """MVP: Mock session check. Returns valid/expired/unknown."""
    pa = get_platform_account(pa_id)
    if pa is None:
        return {"status": "unknown", "account_id": None}
    # MVP: always return valid for active accounts
    status = "valid" if pa.status == "active" else "expired"
    return {"status": status, "account_id": pa.account_id, "platform": pa.platform}


def qr_login_initiate(platform: str) -> dict:
    return start_qr_login(platform)


def qr_login_status(qr_id: str) -> Optional[dict]:
    return poll_qr_login(qr_id)
