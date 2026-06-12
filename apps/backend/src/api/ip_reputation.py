"""IP Reputation API — W17.

Routes:
  POST /ip-reputation/register     — Register a new IP
  GET  /ip-reputation              — List IPs with filters
  GET  /ip-reputation/{ip_id}      — Get IP detail
  PATCH /ip-reputation/{ip_id}     — Update IP fields
  DELETE /ip-reputation/{ip_id}    — Remove IP
  POST /ip-reputation/{ip_id}/anomaly     — Report anomaly
  POST /ip-reputation/{ip_id}/evaluate    — Evaluate trial graduation
  GET  /ip-reputation/{ip_id}/circuit     — Check circuit breaker
  POST /ip-reputation/{ip_id}/recover     — Manual recover
  POST /ip-reputation/{ip_id}/bind        — Bind account
  POST /ip-reputation/{ip_id}/unbind      — Unbind account
  POST /ip-reputation/switch              — Switch account IP
  GET  /ip-reputation/switch-logs         — List switch logs
  GET  /ip-reputation/recommend           — Recommend IP for account
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.services import ip_reputation

router = APIRouter(prefix="/ip-reputation", tags=["ip-reputation"])


# ─── Schemas ───

class RegisterIPRequest(BaseModel):
    address: str
    provider: str
    city: str
    isp: str


class ReportAnomalyRequest(BaseModel):
    anomaly_type: str = Field(..., description="captcha, rate_limit, login_fail, content_removed, account_warning")
    account_id: str
    detail: Optional[str] = None


class BindAccountRequest(BaseModel):
    account_id: str


class SwitchIPRequest(BaseModel):
    account_id: str
    from_ip_id: Optional[str] = None
    to_ip_id: str
    reason: str


class IPResponse(BaseModel):
    ip_id: str
    address: str
    provider: str
    city: str
    isp: str
    status: str
    trust_score: int
    trial_started_at: Optional[str]
    trial_ended_at: Optional[str]
    bound_accounts: List[str]
    anomaly_count: int
    cooldown_until: Optional[str]
    created_at: str
    updated_at: str


class IPSwitchLogResponse(BaseModel):
    log_id: str
    account_id: str
    from_ip_id: Optional[str]
    to_ip_id: str
    reason: str
    switched_at: str


def _to_ip_response(ip: ip_reputation.IPAddress) -> IPResponse:
    return IPResponse(
        ip_id=ip.ip_id,
        address=ip.address,
        provider=ip.provider,
        city=ip.city,
        isp=ip.isp,
        status=ip.status.value,
        trust_score=ip.trust_score,
        trial_started_at=ip.trial_started_at,
        trial_ended_at=ip.trial_ended_at,
        bound_accounts=ip.bound_accounts,
        anomaly_count=len(ip.anomaly_history),
        cooldown_until=ip.cooldown_until,
        created_at=ip.created_at,
        updated_at=ip.updated_at,
    )


# ─── CRUD ───

@router.post("/register", status_code=201, response_model=IPResponse)
def register_ip(req: RegisterIPRequest):
    ip = ip_reputation.register_ip(
        address=req.address,
        provider=req.provider,
        city=req.city,
        isp=req.isp,
    )
    return _to_ip_response(ip)


@router.get("", response_model=List[IPResponse])
def list_ips(
    status: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    min_score: Optional[int] = Query(None),
):
    return [_to_ip_response(ip) for ip in ip_reputation.list_ips(status=status, city=city, min_score=min_score)]


@router.get("/{ip_id}", response_model=IPResponse)
def get_ip(ip_id: str):
    ip = ip_reputation.get_ip(ip_id)
    if not ip:
        raise HTTPException(status_code=404, detail="IP not found")
    return _to_ip_response(ip)


@router.patch("/{ip_id}", response_model=IPResponse)
def update_ip(ip_id: str, body: Dict[str, Any]):
    ip = ip_reputation.update_ip(ip_id, **body)
    if not ip:
        raise HTTPException(status_code=404, detail="IP not found")
    return _to_ip_response(ip)


@router.delete("/{ip_id}", status_code=204)
def delete_ip(ip_id: str):
    ok = ip_reputation.delete_ip(ip_id)
    if not ok:
        raise HTTPException(status_code=404, detail="IP not found")
    return None


# ─── Anomaly & Circuit Breaker ───

@router.post("/{ip_id}/anomaly")
def report_anomaly(ip_id: str, req: ReportAnomalyRequest):
    ip = ip_reputation.get_ip(ip_id)
    if not ip:
        raise HTTPException(status_code=404, detail="IP not found")
    return ip_reputation.report_anomaly(ip_id, req.anomaly_type, req.account_id, req.detail)


@router.post("/{ip_id}/evaluate")
def evaluate_trial(ip_id: str):
    ip = ip_reputation.get_ip(ip_id)
    if not ip:
        raise HTTPException(status_code=404, detail="IP not found")
    return ip_reputation.evaluate_trial(ip_id)


@router.get("/{ip_id}/circuit")
def check_circuit(ip_id: str):
    ip = ip_reputation.get_ip(ip_id)
    if not ip:
        raise HTTPException(status_code=404, detail="IP not found")
    return ip_reputation.check_circuit_breaker(ip_id)


@router.post("/{ip_id}/recover")
def manual_recover(ip_id: str):
    ip = ip_reputation.get_ip(ip_id)
    if not ip:
        raise HTTPException(status_code=404, detail="IP not found")
    return ip_reputation.manual_recover(ip_id)


# ─── Account Binding ───

@router.post("/{ip_id}/bind")
def bind_account(ip_id: str, req: BindAccountRequest):
    ip = ip_reputation.get_ip(ip_id)
    if not ip:
        raise HTTPException(status_code=404, detail="IP not found")
    result = ip_reputation.bind_account(ip_id, req.account_id)
    if not result["success"]:
        raise HTTPException(status_code=409, detail=result["error"])
    return result


@router.post("/{ip_id}/unbind")
def unbind_account(ip_id: str, req: BindAccountRequest):
    ip = ip_reputation.get_ip(ip_id)
    if not ip:
        raise HTTPException(status_code=404, detail="IP not found")
    ok = ip_reputation.unbind_account(ip_id, req.account_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Account not bound to this IP")
    return {"success": True, "account_id": req.account_id, "ip_id": ip_id}


# ─── IP Switching ───

@router.post("/switch")
def switch_ip(req: SwitchIPRequest):
    result = ip_reputation.switch_ip(
        account_id=req.account_id,
        from_ip_id=req.from_ip_id,
        to_ip_id=req.to_ip_id,
        reason=req.reason,
    )
    if not result["success"]:
        raise HTTPException(status_code=409, detail=result["error"])
    return result


@router.get("/switch-logs", response_model=List[IPSwitchLogResponse])
def list_switch_logs(
    account_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    logs = ip_reputation.get_switch_logs(account_id=account_id, limit=limit)
    return [
        IPSwitchLogResponse(
            log_id=l.log_id,
            account_id=l.account_id,
            from_ip_id=l.from_ip_id,
            to_ip_id=l.to_ip_id,
            reason=l.reason,
            switched_at=l.switched_at,
        )
        for l in logs
    ]


# ─── Recommendations ───

@router.get("/recommend")
def recommend_ip(
    account_id: str = Query(...),
    city: Optional[str] = Query(None),
    min_score: int = Query(60, ge=0, le=100),
):
    ip = ip_reputation.recommend_ip_for_account(account_id, city=city, min_score=min_score)
    if not ip:
        raise HTTPException(status_code=404, detail="No suitable IP found")
    return _to_ip_response(ip)
