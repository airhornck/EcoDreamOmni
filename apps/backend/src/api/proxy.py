"""Proxy configuration API routes: CRUD, health check, test."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.core.dependencies import get_current_user
from src.core.database import get_db
from src.models.user import User
from src.services.proxy_service import (
    build_requests_proxies,
    create_proxy,
    delete_proxy_from_db,
    get_proxy,
    list_proxies,
    persist_proxy_to_db,
    remove_proxy,
    update_proxy,
)

router = APIRouter(prefix="/proxies", tags=["proxies"])


# ─── Request/Response Models ───


class CreateProxyRequest(BaseModel):
    name: str
    provider: str = Field(default="custom", description="brightdata, oxylabs, custom, etc.")
    protocol: str = Field(default="http", description="http, https, socks5")
    host: str
    port: int = Field(..., ge=1, le=65535)
    username: str = ""
    password: str = ""
    region: str = ""
    rotation_type: str = Field(default="static", description="static, session, rotating")


class UpdateProxyRequest(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    protocol: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = Field(None, ge=1, le=65535)
    username: Optional[str] = None
    password: Optional[str] = None
    region: Optional[str] = None
    rotation_type: Optional[str] = None
    is_active: Optional[bool] = None


class ProxyResponse(BaseModel):
    id: str
    name: str
    provider: str
    protocol: str
    host: str
    port: int
    username: str
    password: str
    region: str
    rotation_type: str
    is_active: bool
    health_status: str
    last_check_at: Optional[str] = None
    fail_count: int
    success_count: int
    created_at: str
    updated_at: str


class ProxyListResponse(BaseModel):
    proxies: List[ProxyResponse]
    total: int


class ProxyTestResponse(BaseModel):
    success: bool
    proxy_url: str
    error: Optional[str] = None


class ProxyHealthCheckRequest(BaseModel):
    host: str
    port: int = Field(..., ge=1, le=65535)
    username: str = ""
    password: str = ""
    protocol: str = "http"


class ProxyHealthCheckResponse(BaseModel):
    status: str
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    resolved_ip: Optional[str] = None


# ─── Helpers ───


def _to_response(entry) -> ProxyResponse:
    return ProxyResponse(
        id=entry.id,
        name=entry.name,
        provider=entry.provider,
        protocol=entry.protocol,
        host=entry.host,
        port=entry.port,
        username=entry.username,
        password=entry.password,
        region=entry.region,
        rotation_type=entry.rotation_type,
        is_active=entry.is_active,
        health_status=entry.health_status,
        last_check_at=entry.last_check_at,
        fail_count=entry.fail_count,
        success_count=entry.success_count,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


# ─── Routes ───


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ProxyResponse)
async def create_proxy_entry(
    req: CreateProxyRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    entry = create_proxy(
        name=req.name,
        provider=req.provider,
        protocol=req.protocol,
        host=req.host,
        port=req.port,
        username=req.username,
        password=req.password,
        region=req.region,
        rotation_type=req.rotation_type,
    )
    await persist_proxy_to_db(db, entry)
    return _to_response(entry)


@router.get("", response_model=ProxyListResponse)
def list_proxy_entries(user: User = Depends(get_current_user)):
    entries = list_proxies()
    return ProxyListResponse(proxies=[_to_response(e) for e in entries], total=len(entries))


@router.get("/active", response_model=ProxyListResponse)
def list_active_proxies(user: User = Depends(get_current_user)):
    entries = list_proxies(active_only=True)
    return ProxyListResponse(proxies=[_to_response(e) for e in entries], total=len(entries))


@router.get("/{entry_id}", response_model=ProxyResponse)
def get_proxy_entry(entry_id: str, user: User = Depends(get_current_user)):
    entry = get_proxy(entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proxy not found")
    return _to_response(entry)


@router.patch("/{entry_id}", response_model=ProxyResponse)
async def update_proxy_entry(
    entry_id: str,
    req: UpdateProxyRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    kwargs = req.model_dump(exclude_unset=True)
    entry = update_proxy(entry_id, **kwargs)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proxy not found")
    await persist_proxy_to_db(db, entry)
    return _to_response(entry)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_proxy_entry(
    entry_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    removed = remove_proxy(entry_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proxy not found")
    await delete_proxy_from_db(db, entry_id)
    return None


@router.post("/health-check", response_model=ProxyHealthCheckResponse)
def health_check_proxy(req: ProxyHealthCheckRequest, user: User = Depends(get_current_user)):
    """Ad-hoc health check for proxy credentials (before saving them)."""
    import time
    from src.services.proxy_service import build_requests_proxies_from_dict

    proxies = build_requests_proxies_from_dict(req.model_dump())

    try:
        import requests

        start = time.time()
        resp = requests.get(
            "https://httpbin.org/ip",
            proxies=proxies,
            timeout=15,
        )
        elapsed = time.time() - start
        resp.raise_for_status()
        data = resp.json()
        origin_ip = data.get("origin", "unknown")

        return ProxyHealthCheckResponse(
            status="healthy",
            latency_ms=round(elapsed * 1000, 1),
            resolved_ip=origin_ip,
            error=None,
        )
    except Exception as exc:
        return ProxyHealthCheckResponse(
            status="unhealthy",
            latency_ms=None,
            resolved_ip=None,
            error=str(exc),
        )


@router.post("/{entry_id}/test", response_model=ProxyTestResponse)
async def test_proxy_entry(
    entry_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Test proxy connectivity by making a request through it."""
    import time

    entry = get_proxy(entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proxy not found")

    proxies = build_requests_proxies(entry)
    proxy_url = proxies.get("http", "")
    success = False
    error_msg = None

    try:
        import requests

        start = time.time()
        resp = requests.get(
            "https://httpbin.org/ip",
            proxies=proxies,
            timeout=15,
        )
        time.time() - start
        resp.raise_for_status()
        success = True
    except Exception as exc:
        error_msg = str(exc)

    # Update memory cache
    update_proxy(
        entry_id,
        health_status="healthy" if success else "unhealthy",
        last_check_at=__import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat(),
    )
    # Persist to DB (use fresh session to avoid rollback issues)
    await persist_proxy_to_db(db, get_proxy(entry_id))

    return ProxyTestResponse(
        success=success,
        proxy_url=proxy_url,
        error=error_msg,
    )
