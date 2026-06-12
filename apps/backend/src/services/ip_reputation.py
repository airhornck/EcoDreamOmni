"""IP Reputation System — W17 core.

Features:
  - IP trust score (0-100)
  - 7-day trial period for new IPs
  - Dynamic circuit breaker (cooldown per anomaly type)
  - Backup IP switching
  - Max 2 active accounts per IP
  - City/ISP grouping

Anomaly cooldown map (per 文档2 §4.4.3):
  captcha      → 24h
  rate_limit   → 48h
  login_fail   → 72h (manual recovery)
  content_removed → template flagged, IP not penalized
  account_warning → 7d trial recovery
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
import secrets
import uuid


class IPStatus(str, Enum):
    TRIAL = "trial"           # 7-day probation
    ACTIVE = "active"         # Normal operation
    QUARANTINED = "quarantined"  # Circuit breaker tripped
    RETIRED = "retired"       # Permanently banned


class AnomalyType(str, Enum):
    CAPTCHA = "captcha"
    RATE_LIMIT = "rate_limit"
    LOGIN_FAIL = "login_fail"
    CONTENT_REMOVED = "content_removed"
    ACCOUNT_WARNING = "account_warning"


# Cooldown hours per anomaly type
_COOLDOWN_HOURS: Dict[str, int] = {
    AnomalyType.CAPTCHA.value: 24,
    AnomalyType.RATE_LIMIT.value: 48,
    AnomalyType.LOGIN_FAIL.value: 72,
    AnomalyType.ACCOUNT_WARNING.value: 168,  # 7 days
    # content_removed does not penalize IP directly
}

# Score penalties per anomaly type
_SCORE_PENALTY: Dict[str, int] = {
    AnomalyType.CAPTCHA.value: 5,
    AnomalyType.RATE_LIMIT.value: 10,
    AnomalyType.LOGIN_FAIL.value: 15,
    AnomalyType.ACCOUNT_WARNING.value: 20,
    AnomalyType.CONTENT_REMOVED.value: 0,
}


@dataclass
class IPAddress:
    ip_id: str
    address: str
    provider: str
    city: str
    isp: str
    status: IPStatus = IPStatus.TRIAL
    trust_score: int = 50  # Start at 50 in trial
    trial_started_at: Optional[str] = None
    trial_ended_at: Optional[str] = None
    bound_accounts: List[str] = field(default_factory=list)  # account entry IDs
    anomaly_history: List[Dict[str, Any]] = field(default_factory=list)
    cooldown_until: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""


@dataclass
class IPSwitchLog:
    log_id: str
    account_id: str
    from_ip_id: Optional[str]
    to_ip_id: str
    reason: str
    switched_at: str


# In-memory stores
_ip_db: Dict[str, IPAddress] = {}          # ip_id → IPAddress
_ip_by_address: Dict[str, str] = {}        # address → ip_id
_switch_logs: List[IPSwitchLog] = []


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_dt(s: str) -> datetime:
    return datetime.fromisoformat(s)


def _hours_since(s: str) -> float:
    return (_parse_dt(_now()) - _parse_dt(s)).total_seconds() / 3600


# ─── CRUD ───

def register_ip(
    address: str,
    provider: str,
    city: str,
    isp: str,
) -> IPAddress:
    """Register a new IP. Starts in TRIAL status."""
    if address in _ip_by_address:
        ip_id = _ip_by_address[address]
        return _ip_db[ip_id]

    ip_id = str(uuid.uuid4())[:12]
    now = _now()
    ip = IPAddress(
        ip_id=ip_id,
        address=address,
        provider=provider,
        city=city,
        isp=isp,
        status=IPStatus.TRIAL,
        trust_score=50,
        trial_started_at=now,
        bound_accounts=[],
        created_at=now,
        updated_at=now,
    )
    _ip_db[ip_id] = ip
    _ip_by_address[address] = ip_id
    return ip


def get_ip(ip_id: str) -> Optional[IPAddress]:
    return _ip_db.get(ip_id)


def get_ip_by_address(address: str) -> Optional[IPAddress]:
    ip_id = _ip_by_address.get(address)
    return _ip_db.get(ip_id) if ip_id else None


def list_ips(
    status: Optional[str] = None,
    city: Optional[str] = None,
    min_score: Optional[int] = None,
) -> List[IPAddress]:
    ips = list(_ip_db.values())
    if status:
        ips = [ip for ip in ips if ip.status.value == status]
    if city:
        ips = [ip for ip in ips if ip.city == city]
    if min_score is not None:
        ips = [ip for ip in ips if ip.trust_score >= min_score]
    return ips


def update_ip(ip_id: str, **kwargs) -> Optional[IPAddress]:
    ip = _ip_db.get(ip_id)
    if not ip:
        return None
    for key, value in kwargs.items():
        if hasattr(ip, key):
            setattr(ip, key, value)
    ip.updated_at = _now()
    return ip


def delete_ip(ip_id: str) -> bool:
    ip = _ip_db.pop(ip_id, None)
    if ip:
        _ip_by_address.pop(ip.address, None)
        return True
    return False


# ─── Trial period ───

def evaluate_trial(ip_id: str) -> Dict[str, Any]:
    """Evaluate if a trial IP can graduate to ACTIVE.

    Requirements:
      - 7 days elapsed since trial_started_at
      - No anomalies in last 7 days
      - Trust score >= 70
    """
    ip = _ip_db.get(ip_id)
    if not ip:
        return {"success": False, "error": "IP not found"}

    if ip.status != IPStatus.TRIAL:
        return {"success": True, "status": ip.status.value, "reason": "Not in trial"}

    if not ip.trial_started_at:
        return {"success": False, "error": "Trial start date missing"}

    hours_elapsed = _hours_since(ip.trial_started_at)
    if hours_elapsed < 7 * 24:
        return {
            "success": False,
            "reason": "trial_period_incomplete",
            "hours_remaining": (7 * 24) - hours_elapsed,
        }

    # Check anomalies in last 7 days
    recent_anomalies = [
        a for a in ip.anomaly_history
        if _hours_since(a["occurred_at"]) <= 7 * 24
    ]
    if recent_anomalies:
        return {
            "success": False,
            "reason": "recent_anomalies",
            "anomaly_count": len(recent_anomalies),
        }

    if ip.trust_score < 70:
        return {
            "success": False,
            "reason": "trust_score_too_low",
            "current_score": ip.trust_score,
        }

    # Graduate
    ip.status = IPStatus.ACTIVE
    ip.trial_ended_at = _now()
    ip.updated_at = _now()
    return {"success": True, "status": "active", "reason": "trial_passed"}


# ─── Anomaly reporting ───

def report_anomaly(
    ip_id: str,
    anomaly_type: str,
    account_id: str,
    detail: Optional[str] = None,
) -> Dict[str, Any]:
    """Report an anomaly and apply penalties + circuit breaker."""
    ip = _ip_db.get(ip_id)
    if not ip:
        return {"success": False, "error": "IP not found"}

    now = _now()
    record = {
        "anomaly_type": anomaly_type,
        "account_id": account_id,
        "detail": detail,
        "occurred_at": now,
    }
    ip.anomaly_history.append(record)

    # Penalize trust score
    penalty = _SCORE_PENALTY.get(anomaly_type, 0)
    ip.trust_score = max(0, ip.trust_score - penalty)

    # Apply cooldown if applicable
    cooldown_hours = _COOLDOWN_HOURS.get(anomaly_type)
    if cooldown_hours:
        cooldown_dt = datetime.now(timezone.utc) + timedelta(hours=cooldown_hours)
        ip.cooldown_until = cooldown_dt.isoformat()
        ip.status = IPStatus.QUARANTINED

    # Retire if score drops too low
    if ip.trust_score <= 20:
        ip.status = IPStatus.RETIRED

    ip.updated_at = now
    return {
        "success": True,
        "ip_id": ip_id,
        "trust_score": ip.trust_score,
        "status": ip.status.value,
        "cooldown_hours": cooldown_hours,
        "cooldown_until": ip.cooldown_until,
    }


# ─── Circuit breaker ───

def check_circuit_breaker(ip_id: str) -> Dict[str, Any]:
    """Check if an IP is under circuit breaker."""
    ip = _ip_db.get(ip_id)
    if not ip:
        return {"tripped": True, "reason": "IP not found"}

    if ip.status == IPStatus.RETIRED:
        return {"tripped": True, "reason": "retired", "status": "retired"}

    if ip.status == IPStatus.QUARANTINED:
        if ip.cooldown_until:
            remaining_hours = (_parse_dt(ip.cooldown_until) - _parse_dt(_now())).total_seconds() / 3600
            if remaining_hours > 0:
                return {
                    "tripped": True,
                    "reason": "cooldown_active",
                    "remaining_hours": remaining_hours,
                    "status": "quarantined",
                }
            else:
                # Cooldown expired — auto-recover to active if score is acceptable
                if ip.trust_score >= 40:
                    ip.status = IPStatus.ACTIVE
                    ip.cooldown_until = None
                    ip.updated_at = _now()
                    return {"tripped": False, "reason": "cooldown_expired", "status": "active"}
                else:
                    return {"tripped": True, "reason": "trust_score_too_low", "status": "quarantined"}
        else:
            # Quarantined without explicit cooldown — stays quarantined until manual recover
            return {"tripped": True, "reason": "quarantined", "status": "quarantined"}

    return {"tripped": False, "status": ip.status.value}


def manual_recover(ip_id: str) -> Dict[str, Any]:
    """Manual recovery (e.g. after login_fail which requires human check)."""
    ip = _ip_db.get(ip_id)
    if not ip:
        return {"success": False, "error": "IP not found"}

    ip.status = IPStatus.ACTIVE
    ip.cooldown_until = None
    ip.updated_at = _now()
    return {"success": True, "status": ip.status.value}


# ─── Account binding ───

def bind_account(ip_id: str, account_id: str) -> Dict[str, Any]:
    """Bind an account to an IP. Max 2 active accounts per IP."""
    ip = _ip_db.get(ip_id)
    if not ip:
        return {"success": False, "error": "IP not found"}

    cb = check_circuit_breaker(ip_id)
    if cb["tripped"]:
        return {"success": False, "error": f"IP is under circuit breaker: {cb['reason']}"}

    active_accounts = [a for a in ip.bound_accounts]
    if account_id in active_accounts:
        return {"success": True, "bound": True, "reason": "Already bound"}

    if len(active_accounts) >= 2:
        return {"success": False, "error": "IP already bound to 2 accounts (max reached)"}

    ip.bound_accounts.append(account_id)
    ip.updated_at = _now()
    return {"success": True, "bound": True, "account_count": len(ip.bound_accounts)}


def unbind_account(ip_id: str, account_id: str) -> bool:
    ip = _ip_db.get(ip_id)
    if not ip:
        return False
    if account_id in ip.bound_accounts:
        ip.bound_accounts.remove(account_id)
        ip.updated_at = _now()
        return True
    return False


# ─── IP switching ───

def switch_ip(
    account_id: str,
    from_ip_id: Optional[str],
    to_ip_id: str,
    reason: str,
) -> Dict[str, Any]:
    """Switch an account from one IP to another."""
    to_ip = _ip_db.get(to_ip_id)
    if not to_ip:
        return {"success": False, "error": "Target IP not found"}

    cb = check_circuit_breaker(to_ip_id)
    if cb["tripped"]:
        return {"success": False, "error": f"Target IP is under circuit breaker: {cb['reason']}"}

    if len(to_ip.bound_accounts) >= 2:
        return {"success": False, "error": "Target IP already at max capacity (2 accounts)"}

    # Unbind from old IP
    if from_ip_id:
        unbind_account(from_ip_id, account_id)

    # Bind to new IP
    bind_result = bind_account(to_ip_id, account_id)
    if not bind_result["success"]:
        return bind_result

    # Log
    log = IPSwitchLog(
        log_id=str(uuid.uuid4())[:12],
        account_id=account_id,
        from_ip_id=from_ip_id,
        to_ip_id=to_ip_id,
        reason=reason,
        switched_at=_now(),
    )
    _switch_logs.append(log)

    return {
        "success": True,
        "account_id": account_id,
        "to_ip_id": to_ip_id,
        "to_address": to_ip.address,
        "reason": reason,
    }


def get_switch_logs(account_id: Optional[str] = None, limit: int = 50) -> List[IPSwitchLog]:
    logs = _switch_logs
    if account_id:
        logs = [l for l in logs if l.account_id == account_id]
    return logs[-limit:]


# ─── Recommendations ───

def recommend_ip_for_account(
    account_id: str,
    city: Optional[str] = None,
    min_score: int = 60,
) -> Optional[IPAddress]:
    """Recommend the best available IP for an account."""
    candidates = list_ips(status="active", min_score=min_score)
    if city:
        candidates = [ip for ip in candidates if ip.city == city]
    # Exclude IPs already at capacity
    candidates = [ip for ip in candidates if len(ip.bound_accounts) < 2]
    # Exclude already bound to this account
    candidates = [ip for ip in candidates if account_id not in ip.bound_accounts]
    # Sort by trust_score desc
    candidates.sort(key=lambda ip: ip.trust_score, reverse=True)
    return candidates[0] if candidates else None
