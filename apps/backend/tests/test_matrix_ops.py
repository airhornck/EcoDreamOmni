"""Tests for Matrix Operations (W21).

Red-Green TDD for:
  - Account group CRUD
  - Auto-grouping
  - Brief assignment
  - Batch scheduling
  - Group health overview
"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.services import matrix_ops


@pytest.fixture(autouse=True)
def clear_db():
    matrix_ops._groups.clear()
    matrix_ops._assignments.clear()
    matrix_ops._schedules.clear()
    yield


# ─── Group CRUD ───

def test_create_group():
    g = matrix_ops.create_group("Shanghai Growth", {"city": "Shanghai", "lifecycle_phase": "growth"}, ["a1", "a2"])
    assert g.group_id
    assert g.name == "Shanghai Growth"
    assert g.account_ids == ["a1", "a2"]


def test_get_group():
    g = matrix_ops.create_group("Test", {}, ["a1"])
    fetched = matrix_ops.get_group(g.group_id)
    assert fetched is not None
    assert fetched.name == "Test"


def test_list_groups():
    matrix_ops.create_group("G1", {}, ["a1"])
    matrix_ops.create_group("G2", {}, ["a2"])
    assert len(matrix_ops.list_groups()) == 2


def test_delete_group():
    g = matrix_ops.create_group("ToDelete", {}, ["a1"])
    assert matrix_ops.delete_group(g.group_id) is True
    assert matrix_ops.get_group(g.group_id) is None


# ─── Auto-grouping ───

def test_auto_group_accounts():
    accounts = [
        {"id": "a1", "lifecycle_phase": "growth", "city": "Shanghai"},
        {"id": "a2", "lifecycle_phase": "growth", "city": "Shanghai"},
        {"id": "a3", "lifecycle_phase": "cold_start", "city": "Beijing"},
        {"id": "a4", "lifecycle_phase": "cold_start", "city": "Beijing"},
    ]
    groups = matrix_ops.auto_group_accounts(accounts)
    assert len(groups) == 2
    names = {g.name for g in groups}
    assert "growth_Shanghai" in names
    assert "cold_start_Beijing" in names


def test_auto_group_skips_singletons():
    accounts = [
        {"id": "a1", "lifecycle_phase": "growth", "city": "Shanghai"},
        {"id": "a2", "lifecycle_phase": "mature", "city": "Beijing"},
    ]
    groups = matrix_ops.auto_group_accounts(accounts)
    assert len(groups) == 0  # No group with >=2 accounts


# ─── Brief Assignment ───

def test_assign_brief():
    g = matrix_ops.create_group("G", {}, ["a1", "a2"])
    a = matrix_ops.assign_brief_to_group("brief-1", g.group_id)
    assert a.assignment_id
    assert a.brief_id == "brief-1"
    assert a.account_ids == ["a1", "a2"]


def test_assign_brief_missing_group():
    with pytest.raises(ValueError, match="not found"):
        matrix_ops.assign_brief_to_group("brief-1", "nonexistent")


def test_list_assignments():
    g = matrix_ops.create_group("G", {}, ["a1"])
    a = matrix_ops.assign_brief_to_group("b1", g.group_id)
    items = matrix_ops.list_assignments()
    assert len(items) == 1


# ─── Batch Scheduling ───

def test_create_batch_schedule():
    s = matrix_ops.create_batch_schedule("g1", ["t1", "t2", "t3"], stagger_minutes=10)
    assert s.schedule_id
    assert s.task_ids == ["t1", "t2", "t3"]
    assert s.stagger_minutes == 10


def test_list_schedules():
    matrix_ops.create_batch_schedule("g1", ["t1"], 15)
    matrix_ops.create_batch_schedule("g2", ["t2"], 20)
    assert len(matrix_ops.list_batch_schedules()) == 2


# ─── Health Overview ───

def test_group_health_overview():
    g = matrix_ops.create_group("G", {}, ["a1", "a2", "a3"])
    healths = {
        "a1": {"health_score": 90, "status": "active"},
        "a2": {"health_score": 80, "status": "active"},
        "a3": {"health_score": 50, "status": "warming"},
    }
    overview = matrix_ops.group_health_overview(g.group_id, healths)
    assert overview["account_count"] == 3
    assert overview["avg_health_score"] == 73.33  # (90+80+50)/3 rounded
    assert overview["active_count"] == 2
    assert overview["warming_count"] == 1
    assert overview["blocked_count"] == 0


def test_group_health_missing_group():
    result = matrix_ops.group_health_overview("nonexistent", {})
    assert "error" in result
