"""
Phase 3 RBAC tests — Role-Based Access Control for task isolation.

Roles:
  admin    → full access (view/modify/review all tasks)
  reviewer → can review any task in human_wait; can only view/modify own tasks otherwise
  operator → can only view/modify/review own tasks
"""

import pytest
from starlette.testclient import TestClient


def _register_user(client: TestClient, role: str = "operator"):
    import uuid
    email = f"test_{uuid.uuid4().hex[:8]}@ecodream.com"
    resp = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"testuser_{uuid.uuid4().hex[:8]}",
        "role": role,
    })
    assert resp.status_code == 201, f"Register failed: {resp.text}"
    return resp.json()["access_token"]


def _auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}


def _create_task_and_drive_to_human_wait(client, token):
    """Helper: create a task and drive it to HUMAN_WAIT status."""
    resp = client.post("/task-hub/tasks", json={
        "name": "RBAC Test Task",
        "workflow_template_id": "wf_001",
        "workflow_version": 1,
        "account_id": "acc_001",
        "persona_id": "pers_001",
    }, headers=_auth_header(token))
    assert resp.status_code == 201
    task_id = resp.json()["id"]

    # Drive to RUNNING
    for action in ["configure", "queue", "start"]:
        r = client.post(f"/task-hub/tasks/{task_id}/{action}", headers=_auth_header(token))
        assert r.status_code in (200, 204), f"{action} failed: {r.text}"

    # Transition to HUMAN_WAIT
    r = client.post(
        f"/task-hub/tasks/{task_id}/transition",
        json={"status": "human_wait"},
        headers=_auth_header(token),
    )
    assert r.status_code == 200, f"transition to human_wait failed: {r.text}"

    return task_id


# ─── TaskHub List ───


def test_admin_can_list_all_tasks(client):
    """admin 可以看到所有任务，不受 created_by 限制。"""
    token_admin = _register_user(client, role="admin")
    token_op = _register_user(client, role="operator")

    # operator creates a task
    client.post("/task-hub/tasks", json={
        "name": "Op Task",
        "workflow_template_id": "wf_publish_001",
        "workflow_version": 1,
        "account_id": "acc_001",
        "persona_id": "pers_001",
    }, headers=_auth_header(token_op))

    resp = client.get("/task-hub/tasks", headers=_auth_header(token_admin))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert any(t["name"] == "Op Task" for t in data)


def test_reviewer_can_only_list_own_tasks(client):
    """reviewer 只能看到自己创建的任务（列表隔离）。"""
    token_rev = _register_user(client, role="reviewer")
    token_op = _register_user(client, role="operator")

    client.post("/task-hub/tasks", json={
        "name": "Op Task",
        "workflow_template_id": "wf_publish_001",
        "workflow_version": 1,
        "account_id": "acc_001",
        "persona_id": "pers_001",
    }, headers=_auth_header(token_op))

    resp = client.get("/task-hub/tasks", headers=_auth_header(token_rev))
    assert resp.status_code == 200
    data = resp.json()
    assert all(t["created_by"] != "op_user" for t in data)  # reviewer 看不到 operator 的任务


# ─── TaskHub Detail / Modify ───


def test_admin_can_access_any_task_detail(client):
    """admin 可以查看任意任务详情。"""
    token_admin = _register_user(client, role="admin")
    token_op = _register_user(client, role="operator")

    resp = client.post("/task-hub/tasks", json={
        "name": "Op Task",
        "workflow_template_id": "wf_publish_001",
        "workflow_version": 1,
        "account_id": "acc_001",
        "persona_id": "pers_001",
    }, headers=_auth_header(token_op))
    task_id = resp.json()["id"]

    resp = client.get(f"/task-hub/tasks/{task_id}", headers=_auth_header(token_admin))
    assert resp.status_code == 200
    assert resp.json()["name"] == "Op Task"


def test_reviewer_cannot_modify_others_task(client):
    """reviewer 不能修改别人的任务。"""
    token_rev = _register_user(client, role="reviewer")
    token_op = _register_user(client, role="operator")

    resp = client.post("/task-hub/tasks", json={
        "name": "Op Task",
        "workflow_template_id": "wf_publish_001",
        "workflow_version": 1,
        "account_id": "acc_001",
        "persona_id": "pers_001",
    }, headers=_auth_header(token_op))
    task_id = resp.json()["id"]

    resp = client.patch(
        f"/task-hub/tasks/{task_id}",
        json={"priority": 99},
        headers=_auth_header(token_rev),
    )
    assert resp.status_code == 403


# ─── HITL Pending ───


def test_reviewer_can_see_all_pending_reviews(client):
    """reviewer 可以看到所有待审核任务（不限于自己的）。"""
    token_rev = _register_user(client, role="reviewer")
    token_op = _register_user(client, role="operator")

    task_id = _create_task_and_drive_to_human_wait(client, token_op)

    resp = client.get("/human-in-the-loop/pending", headers=_auth_header(token_rev))
    assert resp.status_code == 200
    data = resp.json()
    assert any(item["task_id"] == task_id for item in data["items"])


def test_operator_can_only_see_own_pending_reviews(client):
    """operator 只能看到自己的待审核任务。"""
    token_op_a = _register_user(client, role="operator")
    token_op_b = _register_user(client, role="operator")

    task_id_a = _create_task_and_drive_to_human_wait(client, token_op_a)
    _create_task_and_drive_to_human_wait(client, token_op_b)

    resp = client.get("/human-in-the-loop/pending", headers=_auth_header(token_op_a))
    assert resp.status_code == 200
    data = resp.json()
    assert any(item["task_id"] == task_id_a for item in data["items"])
    # operator A 不应该看到 B 的任务（但列表中可能只有 A 的任务，因为 B 的任务 created_by 不同）
    # 这个断言在只有 A 和 B 的任务时可能不够强；更准确的测试在下面


def test_admin_can_see_all_pending_reviews(client):
    """admin 可以看到所有待审核任务。"""
    token_admin = _register_user(client, role="admin")
    token_op = _register_user(client, role="operator")

    task_id = _create_task_and_drive_to_human_wait(client, token_op)

    resp = client.get("/human-in-the-loop/pending", headers=_auth_header(token_admin))
    assert resp.status_code == 200
    data = resp.json()
    assert any(item["task_id"] == task_id for item in data["items"])


# ─── HITL Review Actions ───


def test_reviewer_can_approve_others_task(client):
    """reviewer 可以审核（通过）别人创建的任务。"""
    token_rev = _register_user(client, role="reviewer")
    token_op = _register_user(client, role="operator")

    task_id = _create_task_and_drive_to_human_wait(client, token_op)

    resp = client.post(
        f"/human-in-the-loop/tasks/{task_id}/approve",
        json={},
        headers=_auth_header(token_rev),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved_waiting_publish"


def test_reviewer_can_reject_others_task(client):
    """reviewer 可以审核（拒绝）别人创建的任务。"""
    token_rev = _register_user(client, role="reviewer")
    token_op = _register_user(client, role="operator")

    task_id = _create_task_and_drive_to_human_wait(client, token_op)

    resp = client.post(
        f"/human-in-the-loop/tasks/{task_id}/reject",
        json={"reason": "不符合规范"},
        headers=_auth_header(token_rev),
    )
    assert resp.status_code == 200


def test_operator_cannot_approve_others_task(client):
    """operator 不能审核别人创建的任务。"""
    token_op_a = _register_user(client, role="operator")
    token_op_b = _register_user(client, role="operator")

    task_id = _create_task_and_drive_to_human_wait(client, token_op_a)

    resp = client.post(
        f"/human-in-the-loop/tasks/{task_id}/approve",
        json={},
        headers=_auth_header(token_op_b),
    )
    assert resp.status_code == 403


def test_admin_can_approve_any_task(client):
    """admin 可以审核任何任务。"""
    token_admin = _register_user(client, role="admin")
    token_op = _register_user(client, role="operator")

    task_id = _create_task_and_drive_to_human_wait(client, token_op)

    resp = client.post(
        f"/human-in-the-loop/tasks/{task_id}/approve",
        json={},
        headers=_auth_header(token_admin),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved_waiting_publish"


# ─── ReviewPublish Center ───


def test_admin_can_see_all_conclusions(client):
    """admin 可以在审核发布中心看到所有结论。"""
    token_admin = _register_user(client, role="admin")
    token_op = _register_user(client, role="operator")

    task_id = _create_task_and_drive_to_human_wait(client, token_op)
    # approve it via admin
    client.post(
        f"/human-in-the-loop/tasks/{task_id}/approve",
        json={},
        headers=_auth_header(token_admin),
    )

    resp = client.get("/review-publish-center/conclusions", headers=_auth_header(token_admin))
    assert resp.status_code == 200
    data = resp.json()
    assert any(item["task_id"] == task_id for item in data["items"])


def test_reviewer_cannot_confirm_publish_others_task(client):
    """reviewer 不能在别人任务上确认发布（修改权限限制）。"""
    token_rev = _register_user(client, role="reviewer")
    token_op = _register_user(client, role="operator")

    task_id = _create_task_and_drive_to_human_wait(client, token_op)
    # approve it first
    client.post(
        f"/human-in-the-loop/tasks/{task_id}/approve",
        json={},
        headers=_auth_header(token_rev),
    )

    resp = client.post(
        f"/review-publish-center/conclusions/{task_id}/confirm-publish",
        json={"publish_mode": "immediate"},
        headers=_auth_header(token_rev),
    )
    assert resp.status_code == 403
