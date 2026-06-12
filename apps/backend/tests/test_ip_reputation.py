"""Tests for IP Reputation System (W17).

Red-Green TDD coverage for:
  - IP registration & CRUD
  - Trial period evaluation
  - Anomaly reporting & trust score penalties
  - Circuit breaker (auto cooldown + manual recovery)
  - Account binding (max 2 per IP)
  - IP switching & logs
  - IP recommendation
"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.services import ip_reputation as ipr
from src.services.ip_reputation import IPStatus, AnomalyType


@pytest.fixture(autouse=True)
def clear_db():
    """Clear in-memory stores before each test."""
    ipr._ip_db.clear()
    ipr._ip_by_address.clear()
    ipr._switch_logs.clear()
    yield


# ─── Registration ───

def test_register_ip():
    ip = ipr.register_ip("192.168.1.1", "provider-a", "Shanghai", "China Telecom")
    assert ip.ip_id
    assert ip.address == "192.168.1.1"
    assert ip.status == IPStatus.TRIAL
    assert ip.trust_score == 50
    assert ip.trial_started_at is not None


def test_register_duplicate_address_returns_existing():
    ip1 = ipr.register_ip("192.168.1.1", "a", "Shanghai", "CT")
    ip2 = ipr.register_ip("192.168.1.1", "b", "Beijing", "CU")
    assert ip1.ip_id == ip2.ip_id


# ─── CRUD ───

def test_get_ip():
    ip = ipr.register_ip("10.0.0.1", "p", "Beijing", "CU")
    fetched = ipr.get_ip(ip.ip_id)
    assert fetched is not None
    assert fetched.address == "10.0.0.1"


def test_list_ips_filter():
    ipr.register_ip("1.1.1.1", "p", "Shanghai", "CT")
    ipr.register_ip("2.2.2.2", "p", "Beijing", "CU")
    shanghai = ipr.list_ips(city="Shanghai")
    assert len(shanghai) == 1
    assert shanghai[0].city == "Shanghai"


def test_update_ip():
    ip = ipr.register_ip("3.3.3.3", "p", "Shenzhen", "CT")
    updated = ipr.update_ip(ip.ip_id, trust_score=80)
    assert updated is not None
    assert updated.trust_score == 80


def test_delete_ip():
    ip = ipr.register_ip("4.4.4.4", "p", "Guangzhou", "CM")
    assert ipr.delete_ip(ip.ip_id) is True
    assert ipr.get_ip(ip.ip_id) is None


# ─── Trial evaluation ───

def test_trial_not_graduated_yet():
    ip = ipr.register_ip("5.5.5.5", "p", "Chengdu", "CT")
    result = ipr.evaluate_trial(ip.ip_id)
    assert result["success"] is False
    assert result["reason"] == "trial_period_incomplete"


def test_trial_graduated():
    ip = ipr.register_ip("6.6.6.6", "p", "Hangzhou", "CT")
    # Fake a 7-day-old trial
    from datetime import datetime, timezone, timedelta
    old = (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
    ip.trial_started_at = old
    ip.trust_score = 75
    result = ipr.evaluate_trial(ip.ip_id)
    assert result["success"] is True
    assert result["status"] == "active"
    assert ip.status == IPStatus.ACTIVE


def test_trial_fails_due_to_low_score():
    ip = ipr.register_ip("7.7.7.7", "p", "Wuhan", "CT")
    from datetime import datetime, timezone, timedelta
    old = (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
    ip.trial_started_at = old
    ip.trust_score = 60  # Below 70
    result = ipr.evaluate_trial(ip.ip_id)
    assert result["success"] is False
    assert result["reason"] == "trust_score_too_low"


# ─── Anomaly reporting ───

def test_anomaly_reduces_trust_score():
    ip = ipr.register_ip("8.8.8.8", "p", "Nanjing", "CT")
    ip.status = IPStatus.ACTIVE
    result = ipr.report_anomaly(ip.ip_id, AnomalyType.CAPTCHA.value, "acc-1")
    assert result["success"] is True
    assert result["trust_score"] == 45  # 50 - 5
    assert result["status"] == "quarantined"
    assert result["cooldown_hours"] == 24


def test_rate_limit_penalty():
    ip = ipr.register_ip("9.9.9.9", "p", "Xian", "CT")
    ip.status = IPStatus.ACTIVE
    result = ipr.report_anomaly(ip.ip_id, AnomalyType.RATE_LIMIT.value, "acc-1")
    assert result["trust_score"] == 40  # 50 - 10
    assert result["cooldown_hours"] == 48


def test_login_fail_penalty():
    ip = ipr.register_ip("10.10.10.10", "p", "Chongqing", "CT")
    ip.status = IPStatus.ACTIVE
    result = ipr.report_anomaly(ip.ip_id, AnomalyType.LOGIN_FAIL.value, "acc-1")
    assert result["trust_score"] == 35  # 50 - 15
    assert result["cooldown_hours"] == 72


def test_account_warning_penalty():
    ip = ipr.register_ip("11.11.11.11", "p", "Tianjin", "CT")
    ip.status = IPStatus.ACTIVE
    result = ipr.report_anomaly(ip.ip_id, AnomalyType.ACCOUNT_WARNING.value, "acc-1")
    assert result["trust_score"] == 30  # 50 - 20
    assert result["cooldown_hours"] == 168


def test_retired_when_score_too_low():
    ip = ipr.register_ip("12.12.12.12", "p", "Qingdao", "CT")
    ip.status = IPStatus.ACTIVE
    ip.trust_score = 25
    result = ipr.report_anomaly(ip.ip_id, AnomalyType.LOGIN_FAIL.value, "acc-1")
    assert result["trust_score"] == 10  # 25 - 15
    assert result["status"] == "retired"  # <= 20 triggers retire


# ─── Circuit breaker ───

def test_circuit_breaker_tripped():
    ip = ipr.register_ip("13.13.13.13", "p", "Dalian", "CT")
    ip.status = IPStatus.ACTIVE
    ipr.report_anomaly(ip.ip_id, AnomalyType.CAPTCHA.value, "acc-1")
    cb = ipr.check_circuit_breaker(ip.ip_id)
    assert cb["tripped"] is True
    assert cb["reason"] == "cooldown_active"


def test_circuit_breaker_expired_auto_recover():
    ip = ipr.register_ip("14.14.14.14", "p", "Suzhou", "CT")
    ip.status = IPStatus.QUARANTINED
    ip.trust_score = 60
    # Set cooldown to expired
    from datetime import datetime, timezone, timedelta
    ip.cooldown_until = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    cb = ipr.check_circuit_breaker(ip.ip_id)
    assert cb["tripped"] is False
    assert cb["status"] == "active"


def test_circuit_breaker_retired():
    ip = ipr.register_ip("15.15.15.15", "p", "Hangzhou", "CT")
    ip.status = IPStatus.RETIRED
    cb = ipr.check_circuit_breaker(ip.ip_id)
    assert cb["tripped"] is True
    assert cb["reason"] == "retired"


def test_manual_recover():
    ip = ipr.register_ip("16.16.16.16", "p", "Ningbo", "CT")
    ip.status = IPStatus.QUARANTINED
    ip.cooldown_until = "2099-01-01T00:00:00+00:00"
    result = ipr.manual_recover(ip.ip_id)
    assert result["success"] is True
    assert result["status"] == "active"
    assert ip.status == IPStatus.ACTIVE
    assert ip.cooldown_until is None


# ─── Account binding ───

def test_bind_account_success():
    ip = ipr.register_ip("17.17.17.17", "p", "Wuxi", "CT")
    ip.status = IPStatus.ACTIVE
    result = ipr.bind_account(ip.ip_id, "acc-a")
    assert result["success"] is True
    assert result["bound"] is True
    assert len(ip.bound_accounts) == 1


def test_bind_account_max_capacity():
    ip = ipr.register_ip("18.18.18.18", "p", "Changsha", "CT")
    ip.status = IPStatus.ACTIVE
    ipr.bind_account(ip.ip_id, "acc-a")
    ipr.bind_account(ip.ip_id, "acc-b")
    result = ipr.bind_account(ip.ip_id, "acc-c")
    assert result["success"] is False
    assert "max" in result["error"].lower()


def test_bind_account_under_circuit_breaker():
    ip = ipr.register_ip("19.19.19.19", "p", "Fuzhou", "CT")
    ip.status = IPStatus.QUARANTINED
    result = ipr.bind_account(ip.ip_id, "acc-a")
    assert result["success"] is False
    assert "circuit" in result["error"].lower()


def test_unbind_account():
    ip = ipr.register_ip("20.20.20.20", "p", "Xiamen", "CT")
    ip.status = IPStatus.ACTIVE
    ipr.bind_account(ip.ip_id, "acc-a")
    ok = ipr.unbind_account(ip.ip_id, "acc-a")
    assert ok is True
    assert "acc-a" not in ip.bound_accounts


# ─── IP switching ───

def test_switch_ip_success():
    from_ip = ipr.register_ip("21.21.21.21", "p", "Shenzhen", "CT")
    from_ip.status = IPStatus.ACTIVE
    to_ip = ipr.register_ip("22.22.22.22", "p", "Shenzhen", "CT")
    to_ip.status = IPStatus.ACTIVE
    ipr.bind_account(from_ip.ip_id, "acc-x")

    result = ipr.switch_ip("acc-x", from_ip.ip_id, to_ip.ip_id, "anomaly detected")
    assert result["success"] is True
    assert result["to_ip_id"] == to_ip.ip_id
    assert "acc-x" in to_ip.bound_accounts
    assert "acc-x" not in from_ip.bound_accounts


def test_switch_ip_to_full_ip_fails():
    from_ip = ipr.register_ip("23.23.23.23", "p", "Guangzhou", "CT")
    from_ip.status = IPStatus.ACTIVE
    to_ip = ipr.register_ip("24.24.24.24", "p", "Guangzhou", "CT")
    to_ip.status = IPStatus.ACTIVE
    ipr.bind_account(to_ip.ip_id, "acc-y")
    ipr.bind_account(to_ip.ip_id, "acc-z")

    result = ipr.switch_ip("acc-x", from_ip.ip_id, to_ip.ip_id, "anomaly")
    assert result["success"] is False
    assert "max" in result["error"].lower()


def test_switch_ip_to_quarantined_fails():
    from_ip = ipr.register_ip("25.25.25.25", "p", "Dongguan", "CT")
    from_ip.status = IPStatus.ACTIVE
    to_ip = ipr.register_ip("26.26.26.26", "p", "Dongguan", "CT")
    to_ip.status = IPStatus.QUARANTINED

    result = ipr.switch_ip("acc-x", from_ip.ip_id, to_ip.ip_id, "anomaly")
    assert result["success"] is False
    assert "circuit" in result["error"].lower()


def test_switch_logs():
    from_ip = ipr.register_ip("27.27.27.27", "p", "Zhuhai", "CT")
    from_ip.status = IPStatus.ACTIVE
    to_ip = ipr.register_ip("28.28.28.28", "p", "Zhuhai", "CT")
    to_ip.status = IPStatus.ACTIVE
    ipr.bind_account(from_ip.ip_id, "acc-m")
    ipr.switch_ip("acc-m", from_ip.ip_id, to_ip.ip_id, "test switch")

    logs = ipr.get_switch_logs(account_id="acc-m")
    assert len(logs) == 1
    assert logs[0].account_id == "acc-m"
    assert logs[0].reason == "test switch"


# ─── Recommendations ───

def test_recommend_ip():
    ip1 = ipr.register_ip("29.29.29.29", "p", "Shanghai", "CT")
    ip1.status = IPStatus.ACTIVE
    ip1.trust_score = 90
    ip2 = ipr.register_ip("30.30.30.30", "p", "Shanghai", "CT")
    ip2.status = IPStatus.ACTIVE
    ip2.trust_score = 80

    rec = ipr.recommend_ip_for_account("acc-new", city="Shanghai")
    assert rec is not None
    assert rec.trust_score == 90  # Higher score first


def test_recommend_ip_excludes_full():
    ip = ipr.register_ip("31.31.31.31", "p", "Beijing", "CT")
    ip.status = IPStatus.ACTIVE
    ip.trust_score = 95
    ipr.bind_account(ip.ip_id, "acc-1")
    ipr.bind_account(ip.ip_id, "acc-2")

    rec = ipr.recommend_ip_for_account("acc-new", city="Beijing")
    assert rec is None  # Full


def test_recommend_ip_excludes_already_bound():
    ip = ipr.register_ip("32.32.32.32", "p", "Hangzhou", "CT")
    ip.status = IPStatus.ACTIVE
    ip.trust_score = 95
    ipr.bind_account(ip.ip_id, "acc-old")

    rec = ipr.recommend_ip_for_account("acc-old", city="Hangzhou")
    assert rec is None  # Already bound


def test_recommend_ip_excludes_trial():
    ip = ipr.register_ip("33.33.33.33", "p", "Nanjing", "CT")
    ip.status = IPStatus.TRIAL
    ip.trust_score = 75

    rec = ipr.recommend_ip_for_account("acc-new", city="Nanjing")
    assert rec is None  # Trial not active
