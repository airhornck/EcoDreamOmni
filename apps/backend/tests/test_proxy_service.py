"""
Proxy service tests: CRUD, proxy dict builder, health tracking.
"""

import pytest
from src.models.proxy_config import clear_proxy_entries
from src.services.proxy_service import (
    build_requests_proxies,
    build_requests_proxies_from_dict,
    create_proxy,
    get_proxy,
    list_proxies,
    pick_proxy_for_region,
    record_proxy_result,
    remove_proxy,
    update_proxy,
)


@pytest.fixture(autouse=True)
def clean_proxy_db():
    clear_proxy_entries()
    yield
    clear_proxy_entries()


def test_create_proxy():
    entry = create_proxy(
        name="BrightData US",
        provider="brightdata",
        protocol="http",
        host="proxy.example.com",
        port=8080,
        username="user",
        password="pass",
        region="us",
        rotation_type="rotating",
    )
    assert entry.id
    assert entry.name == "BrightData US"
    assert entry.provider == "brightdata"
    assert entry.protocol == "http"
    assert entry.host == "proxy.example.com"
    assert entry.port == 8080
    assert entry.username == "user"
    assert entry.password == "pass"
    assert entry.region == "us"
    assert entry.rotation_type == "rotating"
    assert entry.is_active is True
    assert entry.health_status == "unknown"


def test_get_proxy():
    entry = create_proxy(name="Test", provider="custom", protocol="http", host="1.1.1.1", port=80)
    found = get_proxy(entry.id)
    assert found is not None
    assert found.id == entry.id
    assert get_proxy("nonexistent") is None


def test_list_proxies():
    create_proxy(name="P1", provider="custom", protocol="http", host="1.1.1.1", port=80)
    create_proxy(name="P2", provider="custom", protocol="http", host="2.2.2.2", port=80, region="us")
    entries = list_proxies()
    assert len(entries) == 2


def test_list_active_proxies():
    p1 = create_proxy(name="P1", provider="custom", protocol="http", host="1.1.1.1", port=80)
    p2 = create_proxy(name="P2", provider="custom", protocol="http", host="2.2.2.2", port=80)
    update_proxy(p2.id, is_active=False)
    entries = list_proxies(active_only=True)
    assert len(entries) == 1
    assert entries[0].id == p1.id


def test_update_proxy():
    entry = create_proxy(name="Old", provider="custom", protocol="http", host="1.1.1.1", port=80)
    updated = update_proxy(entry.id, name="New", host="2.2.2.2")
    assert updated is not None
    assert updated.name == "New"
    assert updated.host == "2.2.2.2"
    assert update_proxy("nonexistent", name="X") is None


def test_remove_proxy():
    entry = create_proxy(name="Test", provider="custom", protocol="http", host="1.1.1.1", port=80)
    assert remove_proxy(entry.id) is True
    assert get_proxy(entry.id) is None
    assert remove_proxy("nonexistent") is False


def test_build_requests_proxies():
    entry = create_proxy(
        name="AuthProxy",
        provider="custom",
        protocol="http",
        host="proxy.test",
        port=3128,
        username="user",
        password="pass",
    )
    proxies = build_requests_proxies(entry)
    assert proxies["http"] == "http://user:pass@proxy.test:3128"
    assert proxies["https"] == "http://user:pass@proxy.test:3128"


def test_build_requests_proxies_no_auth():
    entry = create_proxy(name="Open", provider="custom", protocol="http", host="open.proxy", port=8080)
    proxies = build_requests_proxies(entry)
    assert proxies["http"] == "http://open.proxy:8080"


def test_build_requests_proxies_socks5():
    entry = create_proxy(name="Socks", provider="custom", protocol="socks5", host="socks.proxy", port=1080)
    proxies = build_requests_proxies(entry)
    assert proxies["http"] == "socks5://socks.proxy:1080"


def test_build_requests_proxies_from_dict():
    proxies = build_requests_proxies_from_dict(
        {"protocol": "http", "host": "d.test", "port": 8080, "username": "u", "password": "p"}
    )
    assert proxies["http"] == "http://u:p@d.test:8080"


def test_pick_proxy_for_region_exact_match():
    p_us = create_proxy(name="US", provider="custom", protocol="http", host="us.proxy", port=80, region="us")
    p_cn = create_proxy(name="CN", provider="custom", protocol="http", host="cn.proxy", port=80, region="cn")
    picked = pick_proxy_for_region("us")
    assert picked is not None
    assert picked.id == p_us.id


def test_pick_proxy_for_region_fallback():
    create_proxy(name="Only", provider="custom", protocol="http", host="only.proxy", port=80, region="jp")
    picked = pick_proxy_for_region("xx")
    assert picked is not None


def test_pick_proxy_for_region_empty():
    assert pick_proxy_for_region("us") is None


def test_record_proxy_result_success():
    entry = create_proxy(name="H", provider="custom", protocol="http", host="h.test", port=80)
    record_proxy_result(entry.id, success=True)
    p = get_proxy(entry.id)
    assert p.success_count == 1
    assert p.fail_count == 0
    assert p.health_status == "healthy"


def test_record_proxy_result_failure_then_unhealthy():
    entry = create_proxy(name="H", provider="custom", protocol="http", host="h.test", port=80)
    for _ in range(5):
        record_proxy_result(entry.id, success=False)
    p = get_proxy(entry.id)
    assert p.fail_count == 5
    assert p.health_status == "unhealthy"


def test_record_proxy_result_unknown_proxy():
    # Should not raise
    record_proxy_result("nonexistent", success=True)
