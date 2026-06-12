"""Phase 3 Tests — W23-W27 combined.

Covers:
  - Tenant management (W23)
  - Orchestrator shards (W24)
  - API Platform keys/webhooks/rate-limit (W25)
  - Metrics endpoint (W26)
  - Audit logging (W27)
"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.services import tenant_service, orchestrator, api_platform, audit_logger, matrix_ops


@pytest.fixture(autouse=True)
def clear_all():
    tenant_service.tenant_db.clear()
    tenant_service.tenant_slug_index.clear()
    matrix_ops._groups.clear()
    matrix_ops._assignments.clear()
    matrix_ops._schedules.clear()
    orchestrator._shards.clear()
    api_platform._api_keys.clear()
    api_platform._key_hash_index.clear()
    api_platform._webhooks.clear()
    api_platform._rate_limit_buckets.clear()
    audit_logger._audit_db.clear()
    yield


# ─── W23: Tenant ───

def test_tenant_lifecycle():
    t = tenant_service.create_tenant("BrandX", "brandx", max_accounts=10)
    assert t.tenant_id
    assert tenant_service.get_tenant(t.tenant_id) is not None
    tenant_service.update_tenant(t.tenant_id, status="suspended")
    assert tenant_service.get_tenant(t.tenant_id).status == "suspended"
    tenant_service.delete_tenant(t.tenant_id)
    assert tenant_service.get_tenant(t.tenant_id) is None


def test_tenant_platform_allowance():
    t = tenant_service.create_tenant("A", "a", allowed_platforms=["xhs"])
    assert tenant_service.is_platform_allowed(t.tenant_id, "xhs") is True
    assert tenant_service.is_platform_allowed(t.tenant_id, "douyin") is False


# ─── W24: Orchestrator ───

def test_create_group_schedule():
    g = matrix_ops.create_group("G1", {"city": "SH"}, ["acc1", "acc2", "acc3"])
    shards = orchestrator.create_group_schedule(g.group_id, {"brief_id": "b1"}, stagger_minutes=10)
    assert len(shards) == 3
    assert all(s.status == "scheduled" for s in shards)


def test_group_health_check():
    g = matrix_ops.create_group("G2", {}, ["a1", "a2"])
    health = orchestrator.group_health_check(g.group_id)
    assert health["healthy"] is True
    assert health["account_count"] == 2


# ─── W25: API Platform ───

def test_api_key_lifecycle():
    result = api_platform.create_api_key("t1", "Prod Key", ["read", "write"])
    assert "api_key" in result
    key_id = result["key_id"]
    assert len(api_platform.list_api_keys("t1")) == 1
    api_platform.revoke_api_key(key_id)
    assert api_platform.list_api_keys("t1")[0].revoked is True


def test_webhook_lifecycle():
    wh = api_platform.register_webhook("t1", "https://example.com/hook", ["publish"])
    assert wh.webhook_id
    assert wh.secret
    assert len(api_platform.list_webhooks("t1")) == 1
    api_platform.delete_webhook(wh.webhook_id)
    assert len(api_platform.list_webhooks("t1")) == 0


def test_rate_limit():
    for _ in range(105):
        api_platform.check_rate_limit("t1", "api", max_requests=100)
    result = api_platform.check_rate_limit("t1", "api", max_requests=100)
    assert result["allowed"] is False
    assert result["remaining"] == 0


# ─── W26: Metrics (smoke test via import) ───

def test_metrics_functions():
    from src.api.metrics import inc_counter, observe_histogram, set_gauge
    inc_counter("requests_total", {"method": "GET"})
    observe_histogram("request_duration_seconds", 0.05)
    set_gauge("active_users", 42.0)
    # Smoke test passed if no exception


# ─── W27: Audit Logger ───

def test_audit_log_append_only():
    entry = audit_logger.log_event(
        tenant_id="t1",
        actor_id="user-1",
        actor_type="user",
        event_type="content_publish",
        resource_type="content",
        resource_id="c1",
        action="publish",
    )
    assert entry.log_id.startswith("aud_")
    assert audit_logger.count_logs("t1") == 1

    logs = audit_logger.query_logs(tenant_id="t1", event_type="content_publish")
    assert len(logs) == 1
    assert logs[0].resource_id == "c1"


def test_audit_log_query_filtering():
    audit_logger.log_event("t1", "u1", "user", "login", "session", "s1", "login")
    audit_logger.log_event("t1", "u2", "user", "logout", "session", "s2", "logout")
    audit_logger.log_event("t2", "u1", "user", "login", "session", "s3", "login")

    assert audit_logger.count_logs("t1") == 2
    assert audit_logger.count_logs("t2") == 1

    logs = audit_logger.query_logs(actor_id="u1")
    assert len(logs) == 2
