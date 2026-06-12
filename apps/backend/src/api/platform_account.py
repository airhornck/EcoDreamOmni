"""Platform Account API routes: CRUD, cookie vault, QR login, session check."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.core.dependencies import get_current_user
from src.models.user import User
from src.services.platform_account_service import (
    check_session_status,
    create_account,
    get_account,
    list_accounts,
    qr_login_initiate,
    qr_login_status,
    remove_account,
    update_account,
)

router = APIRouter(prefix="/platform-accounts", tags=["platform-accounts"])


# ─── Request/Response Models ───


class CreatePlatformAccountRequest(BaseModel):
    platform: str = Field(..., description="Platform type: xhs, douyin, wechat_channels")
    account_id: str
    nickname: str
    cookie: str
    status: str = "active"


class UpdatePlatformAccountRequest(BaseModel):
    cookie: Optional[str] = None
    nickname: Optional[str] = None
    status: Optional[str] = None


class PlatformAccountResponse(BaseModel):
    id: str
    platform: str
    account_id: str
    nickname: str
    status: str
    created_at: str
    updated_at: str
    last_checked_at: Optional[str] = None
    health_score: float


class PlatformAccountListResponse(BaseModel):
    accounts: List[PlatformAccountResponse]


class SessionStatusResponse(BaseModel):
    status: str
    account_id: Optional[str] = None
    platform: Optional[str] = None


class QRLoginStartRequest(BaseModel):
    platform: str


class QRLoginStartResponse(BaseModel):
    qr_id: str
    qr_url: str
    platform: str


class QRLoginPollResponse(BaseModel):
    qr_id: str
    status: str
    platform: str


# ─── Helpers ───


def _to_response(pa) -> PlatformAccountResponse:
    return PlatformAccountResponse(
        id=pa.id,
        platform=pa.platform,
        account_id=pa.account_id,
        nickname=pa.nickname,
        status=pa.status,
        created_at=pa.created_at,
        updated_at=pa.updated_at,
        last_checked_at=pa.last_checked_at,
        health_score=pa.health_score,
    )


# ─── Routes ───


@router.post("", status_code=status.HTTP_201_CREATED, response_model=PlatformAccountResponse)
def create_platform_account(
    req: CreatePlatformAccountRequest,
    user: User = Depends(get_current_user),
):
    pa = create_account(
        platform=req.platform,
        account_id=req.account_id,
        nickname=req.nickname,
        cookie=req.cookie,
        status=req.status,
    )
    return _to_response(pa)


@router.get("", response_model=PlatformAccountListResponse)
def list_platform_accounts(user: User = Depends(get_current_user)):
    accounts = list_accounts()
    return PlatformAccountListResponse(accounts=[_to_response(a) for a in accounts])


@router.get("/{pa_id}", response_model=PlatformAccountResponse)
def get_platform_account_detail(
    pa_id: str,
    user: User = Depends(get_current_user),
):
    pa = get_account(pa_id)
    if pa is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Platform account not found")
    return _to_response(pa)


@router.patch("/{pa_id}", response_model=PlatformAccountResponse)
def update_platform_account(
    pa_id: str,
    req: UpdatePlatformAccountRequest,
    user: User = Depends(get_current_user),
):
    kwargs = req.model_dump(exclude_unset=True)
    pa = update_account(pa_id, **kwargs)
    if pa is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Platform account not found")
    return _to_response(pa)


@router.delete("/{pa_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_platform_account(
    pa_id: str,
    user: User = Depends(get_current_user),
):
    removed = remove_account(pa_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Platform account not found")
    return None


@router.get("/{pa_id}/session-status", response_model=SessionStatusResponse)
def session_status(
    pa_id: str,
    user: User = Depends(get_current_user),
):
    result = check_session_status(pa_id)
    return SessionStatusResponse(**result)


@router.post("/qr-login/start", response_model=QRLoginStartResponse)
def qr_login_start(
    req: QRLoginStartRequest,
    user: User = Depends(get_current_user),
):
    result = qr_login_initiate(req.platform)
    return QRLoginStartResponse(**result)


@router.get("/qr-login/poll", response_model=QRLoginPollResponse)
def qr_login_poll(
    qr_id: str,
    platform: str,
    user: User = Depends(get_current_user),
):
    result = qr_login_status(qr_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QR login not found")
    return QRLoginPollResponse(**result)
