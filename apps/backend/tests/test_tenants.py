"""Tests for Tenant Management (W23).

Red-Green TDD for:
  - Tenant CRUD
  - Slug uniqueness
  - Config overrides
  - Platform allowance check
  - Account capacity gate
"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.services import tenant_service as ts


@pytest.fixture(autouse=True)
def clear_db():
    ts.tenant_db.clear()
    ts.tenant_slug_index.clear()
    yield


# ─── CRUD ───

def test_create_tenant():
    t = ts.create_tenant("Brand A", "brand-a", max_accounts=10)
    assert t.tenant_id.startswith("tnt_")
    assert t.name == "Brand A"
    assert t.slug == "brand-a"
    assert t.max_accounts == 10
    assert t.status == "active"


def test_create_tenant_duplicate_slug():
    ts.create_tenant("Brand A", "brand-a")
    with pytest.raises(ValueError, match="already exists"):
        ts.create_tenant("Brand B", "brand-a")


def test_get_tenant():
    t = ts.create_tenant("T", "t")
    fetched = ts.get_tenant(t.tenant_id)
    assert fetched is not None
    assert fetched.name == "T"


def test_get_tenant_by_slug():
    t = ts.create_tenant("T", "t")
    fetched = ts.get_tenant_by_slug("t")
    assert fetched is not None
    assert fetched.tenant_id == t.tenant_id


def test_list_tenants():
    ts.create_tenant("A", "a")
    ts.create_tenant("B", "b", config={"x": 1})
    assert len(ts.list_tenants()) == 2


def test_list_tenants_filter_status():
    t = ts.create_tenant("A", "a")
    ts.update_tenant(t.tenant_id, status="suspended")
    assert len(ts.list_tenants(status="active")) == 0
    assert len(ts.list_tenants(status="suspended")) == 1


def test_update_tenant():
    t = ts.create_tenant("A", "a")
    updated = ts.update_tenant(t.tenant_id, name="A2", max_accounts=100)
    assert updated.name == "A2"
    assert updated.max_accounts == 100


def test_delete_tenant():
    t = ts.create_tenant("A", "a")
    assert ts.delete_tenant(t.tenant_id) is True
    assert ts.get_tenant(t.tenant_id) is None


# ─── Platform allowance ───

def test_is_platform_allowed():
    t = ts.create_tenant("A", "a", allowed_platforms=["xhs", "douyin"])
    assert ts.is_platform_allowed(t.tenant_id, "xhs") is True
    assert ts.is_platform_allowed(t.tenant_id, "douyin") is True
    assert ts.is_platform_allowed(t.tenant_id, "wechat_channels") is False


def test_is_platform_allowed_missing_tenant():
    assert ts.is_platform_allowed("nonexistent", "xhs") is False


# ─── Account capacity ───

def test_can_add_account():
    t = ts.create_tenant("A", "a", max_accounts=2)
    assert ts.can_add_account(t.tenant_id, 1) is True
    assert ts.can_add_account(t.tenant_id, 2) is False


# ─── Config overrides ───

def test_get_set_config():
    t = ts.create_tenant("A", "a")
    assert ts.set_tenant_config(t.tenant_id, "publish_frequency", "daily") is True
    assert ts.get_tenant_config(t.tenant_id, "publish_frequency") == "daily"
    assert ts.get_tenant_config(t.tenant_id, "missing", "default") == "default"


def test_config_missing_tenant():
    assert ts.get_tenant_config("nonexistent", "key", "fallback") == "fallback"
    assert ts.set_tenant_config("nonexistent", "key", "val") is False
