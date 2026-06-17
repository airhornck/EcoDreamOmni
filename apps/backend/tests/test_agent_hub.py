"""Tests for AgentHub (W15).

Red-Green TDD for:
  - Agent registration CRUD
  - Config versioning (create/activate/rollback)
  - Dependency declaration & health check
  - Permission grant/revoke/check
"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.services import agent_hub as ah
from src.services.agent_hub import AgentStatus, ConfigStatus, DepStatus, DepType


@pytest.fixture(autouse=True)
def clear_db():
    ah._agent_db.clear()
    ah._config_db.clear()
    ah._dep_db.clear()
    ah._perm_db.clear()
    yield


# ─── Registration ───

def test_register_agent():
    a = ah.register_agent("ContentForge-A1", "CONTENT_FORGE", "Generates content", "alice@corp.com")
    assert a.id.startswith("agt_")
    assert a.name == "ContentForge-A1"
    assert a.role == "CONTENT_FORGE"
    assert a.status == AgentStatus.REGISTERED


def test_get_agent():
    a = ah.register_agent("T", "TEST")
    fetched = ah.get_agent(a.id)
    assert fetched is not None
    assert fetched.name == "T"


def test_list_agents_filter():
    ah.register_agent("A1", "CONTENT_FORGE")
    ah.register_agent("A2", "COMPLIANCE_GUARD")
    ah.register_agent("A3", "CONTENT_FORGE")
    cf = ah.list_agents(role="CONTENT_FORGE")
    assert len(cf) == 2


def test_update_agent():
    a = ah.register_agent("A", "TEST")
    updated = ah.update_agent(a.id, status="active", owner="bob")
    assert updated.status == AgentStatus.ACTIVE
    assert updated.owner == "bob"


def test_deregister_agent():
    a = ah.register_agent("A", "TEST")
    assert ah.deregister_agent(a.id) is True
    assert ah.get_agent(a.id).status == AgentStatus.OFFLINE


# ─── Config Versioning ───

def test_create_config():
    a = ah.register_agent("A", "TEST")
    c = ah.create_config(a.id, "prod", {"timeout": 30}, created_by="alice")
    assert c is not None
    assert c.version == 1
    assert c.status == ConfigStatus.DRAFT
    assert c.checksum


def test_config_versions_increment():
    a = ah.register_agent("A", "TEST")
    c1 = ah.create_config(a.id, "prod", {"timeout": 30})
    c2 = ah.create_config(a.id, "prod", {"timeout": 60})
    assert c1.version == 1
    assert c2.version == 2


def test_activate_config():
    a = ah.register_agent("A", "TEST")
    ah.create_config(a.id, "prod", {"timeout": 30})
    ah.create_config(a.id, "prod", {"timeout": 60})
    ah.activate_config(a.id, 1)
    assert ah.get_config(a.id, 1).status == ConfigStatus.ACTIVE
    assert ah.get_active_config(a.id).version == 1


def test_activate_archives_previous():
    a = ah.register_agent("A", "TEST")
    ah.create_config(a.id, "prod", {"timeout": 30})
    ah.create_config(a.id, "prod", {"timeout": 60})
    ah.activate_config(a.id, 1)
    ah.activate_config(a.id, 2)
    assert ah.get_config(a.id, 1).status == ConfigStatus.ARCHIVED
    assert ah.get_config(a.id, 2).status == ConfigStatus.ACTIVE


def test_rollback_config():
    a = ah.register_agent("A", "TEST")
    ah.create_config(a.id, "prod", {"timeout": 30})
    ah.create_config(a.id, "prod", {"timeout": 60})
    ah.activate_config(a.id, 2)
    ah.rollback_config(a.id, 1)
    assert ah.get_active_config(a.id).version == 1


def test_get_active_config_none():
    a = ah.register_agent("A", "TEST")
    assert ah.get_active_config(a.id) is None


# ─── Dependencies ───

def test_declare_dependency():
    a = ah.register_agent("A", "TEST")
    dep = ah.declare_dependency(a.id, "llm", "gpt-4o-mini")
    assert dep.dep_type == DepType.LLM
    assert dep.dep_name == "gpt-4o-mini"


def test_list_dependencies():
    a = ah.register_agent("A", "TEST")
    ah.declare_dependency(a.id, "llm", "gpt-4o-mini")
    ah.declare_dependency(a.id, "tool", "xhs-connector")
    assert len(ah.list_dependencies(a.id)) == 2


def test_update_dep_status():
    a = ah.register_agent("A", "TEST")
    ah.declare_dependency(a.id, "llm", "gpt-4o-mini")
    assert ah.update_dep_status(a.id, "gpt-4o-mini", "healthy") is True
    assert ah.list_dependencies(a.id)[0].dep_status == DepStatus.HEALTHY


def test_health_check_degrades_agent():
    a = ah.register_agent("A", "TEST")
    ah.declare_dependency(a.id, "llm", "gpt-4o-mini")
    ah.update_dep_status(a.id, "gpt-4o-mini", "down")
    result = ah.check_all_dependencies(a.id)
    assert result["down"] == 1
    assert result["overall"] == "down"
    assert ah.get_agent(a.id).status == AgentStatus.DEGRADED


def test_health_check_healthy():
    a = ah.register_agent("A", "TEST")
    ah.declare_dependency(a.id, "llm", "gpt-4o-mini")
    ah.update_dep_status(a.id, "gpt-4o-mini", "healthy")
    result = ah.check_all_dependencies(a.id)
    assert result["overall"] == "healthy"


# ─── Permissions ───

def test_grant_permission():
    a = ah.register_agent("A", "TEST")
    p = ah.grant_permission(a.id, "alice", "USER", ["READ", "INVOKE"], "admin")
    assert p.principal == "alice"
    assert "INVOKE" in p.actions


def test_check_permission():
    a = ah.register_agent("A", "TEST")
    ah.grant_permission(a.id, "alice", "USER", ["READ"], "admin")
    assert ah.check_permission(a.id, "alice", "READ") is True
    assert ah.check_permission(a.id, "alice", "DELETE") is False
    assert ah.check_permission(a.id, "bob", "READ") is False


def test_revoke_permission():
    a = ah.register_agent("A", "TEST")
    p = ah.grant_permission(a.id, "alice", "USER", ["READ"], "admin")
    assert ah.revoke_permission(a.id, p.id) is True
    assert ah.check_permission(a.id, "alice", "READ") is False


def test_expired_permission():
    a = ah.register_agent("A", "TEST")
    ah.grant_permission(a.id, "alice", "USER", ["READ"], "admin", expires_at="2020-01-01T00:00:00+00:00")
    assert ah.check_permission(a.id, "alice", "READ") is False


# ─── Integration: full lifecycle ───

def test_full_agent_lifecycle():
    # Register
    a = ah.register_agent("Publisher-Main", "PUBLISHER", "Auto publisher", "ops@corp.com")
    # Config versions
    ah.create_config(a.id, "prod", {"timeout": 60, "retries": 3}, "alice")
    ah.create_config(a.id, "prod", {"timeout": 90, "retries": 5}, "bob")
    ah.activate_config(a.id, 1)
    assert ah.get_active_config(a.id).version == 1
    # Dependencies
    ah.declare_dependency(a.id, "llm", "gpt-4o")
    ah.declare_dependency(a.id, "tool", "xhs-publisher-api")
    ah.update_dep_status(a.id, "gpt-4o", "healthy")
    ah.update_dep_status(a.id, "xhs-publisher-api", "healthy")
    health = ah.check_all_dependencies(a.id)
    assert health["overall"] == "healthy"
    # Permissions
    ah.grant_permission(a.id, "orchestrator", "SERVICE", ["INVOKE"], "admin")
    assert ah.check_permission(a.id, "orchestrator", "INVOKE") is True
    # Deregister
    ah.deregister_agent(a.id)
    assert ah.get_agent(a.id).status == AgentStatus.OFFLINE
