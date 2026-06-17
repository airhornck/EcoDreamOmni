"""
W7 Publisher Red-Green tests.
Tests for publish scheduling, staggered dispatch, L3 evaluation, and Playwright publishing.
"""

def get_auth_token(client, role: str = "operator"):
    import uuid
    email = f"test_{uuid.uuid4().hex[:8]}@ecodream.com"
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"testuser_{uuid.uuid4().hex[:8]}",
        "role": "operator",
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]


def _create_approved_hub_task(client, token, draft_id, account_id, platform="xhs"):
    """Helper: create task_hub task and drive to APPROVED_WAITING_PUBLISH."""
    headers = {"Authorization": f"Bearer {token}"}
    r = client.post(
        "/task-hub/tasks",
        json={
            "name": "Test Publish",
            "workflow_template_id": "wf_001",
            "workflow_version": 1,
            "account_id": account_id,
            "persona_id": "p1",
            "platform": platform,
            "created_by": "test",
            "prompt_variables": {"draft_id": draft_id},
        },
        headers=headers,
    )
    assert r.status_code == 201
    tid = r.json()["id"]
    for endpoint in [f"/task-hub/tasks/{tid}/configure", f"/task-hub/tasks/{tid}/queue", f"/task-hub/tasks/{tid}/start"]:
        assert client.post(endpoint, headers=headers).status_code == 200
    assert client.post(
        f"/task-hub/tasks/{tid}/transition", json={"status": "human_wait"}, headers=headers
    ).status_code == 200
    r = client.post(
        f"/task-hub/tasks/{tid}/human-decision",
        json={"decision": "APPROVE", "operator": "test"},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["status"] == "approved_waiting_publish"
    return tid


# ─── Publish Task CRUD ───


def test_create_publish_task(client):
    token = get_auth_token(client)
    hub_task_id = _create_approved_hub_task(client, token, "draft_001", "pool_xhs_001")
    payload = {
        "draft_id": "draft_001",
        "account_id": "pool_xhs_001",
        "platform": "xhs",
        "scheduled_at": "2026-05-15T10:00:00+08:00",
        "task_hub_task_id": hub_task_id,
    }
    response = client.post("/publish-tasks", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert data["draft_id"] == "draft_001"
    assert data["account_id"] == "pool_xhs_001"
    assert data["status"] in ("pending", "scheduled", "skipped")
    assert "id" in data


def test_create_task_requires_auth(client):
    response = client.post("/publish-tasks", json={"draft_id": "x", "account_id": "a"})
    assert response.status_code == 401


def test_list_publish_tasks(client):
    from src.models.publish_task import clear_tasks
    from src.services.publish_scheduler import clear_schedule_log

    clear_tasks()
    clear_schedule_log()
    token = get_auth_token(client)
    hub1 = _create_approved_hub_task(client, token, "d1", "a1")
    hub2 = _create_approved_hub_task(client, token, "d2", "a2", platform="douyin")
    client.post(
        "/publish-tasks",
        json={"draft_id": "d1", "account_id": "a1", "platform": "xhs", "task_hub_task_id": hub1},
        headers={"Authorization": f"Bearer {token}"},
    )
    client.post(
        "/publish-tasks",
        json={"draft_id": "d2", "account_id": "a2", "platform": "douyin", "task_hub_task_id": hub2},
        headers={"Authorization": f"Bearer {token}"},
    )
    response = client.get("/publish-tasks", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["tasks"]) == 2


def test_get_task_detail(client):
    token = get_auth_token(client)
    hub_id = _create_approved_hub_task(client, token, "d3", "a3")
    create_resp = client.post(
        "/publish-tasks",
        json={"draft_id": "d3", "account_id": "a3", "platform": "xhs", "task_hub_task_id": hub_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    task_id = create_resp.json()["id"]
    response = client.get(f"/publish-tasks/{task_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["draft_id"] == "d3"


def test_cancel_task(client):
    token = get_auth_token(client)
    hub_id = _create_approved_hub_task(client, token, "d4", "a4")
    create_resp = client.post(
        "/publish-tasks",
        json={"draft_id": "d4", "account_id": "a4", "platform": "xhs", "task_hub_task_id": hub_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    task_id = create_resp.json()["id"]
    response = client.patch(
        f"/publish-tasks/{task_id}",
        json={"status": "cancelled"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


# ─── L3 Evaluation ───


def test_publisher_l3_rejects_over_limit_account(client):
    """Red: Publisher should skip task when L3 frequency limit is reached."""
    from src.models.account_pool import clear_pool_entries, create_pool_entry
    from src.models.publish_task import clear_tasks
    from src.services.publish_scheduler import clear_schedule_log

    clear_pool_entries()
    clear_tasks()
    clear_schedule_log()

    # Create a cold_start account (limit = 1)
    account = create_pool_entry(
        platform="xhs",
        account_id="cold_acc_001",
        nickname="Test",
        cookie="mock_cookie",
        persona="cat",
        content_vertical="health",
        lifecycle_phase="cold_start",
        fingerprint_profile={
            "user_agent": "ua",
            "viewport": {"width": 1280, "height": 720},
            "locale": "zh-CN",
            "timezone": "Asia/Shanghai",
        },
    )

    token = get_auth_token(client)

    # First task should schedule (or be allowed by evaluate_l3)
    hub1 = _create_approved_hub_task(client, token, "d_l3_1", account.id)
    resp1 = client.post(
        "/publish-tasks",
        json={"draft_id": "d_l3_1", "account_id": account.id, "platform": "xhs", "task_hub_task_id": hub1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp1.status_code == 201
    resp1.json()
    # After scheduling, the task exists; second task should be skipped by evaluate_l3
    # because daily count from task db >= limit (1)
    hub2 = _create_approved_hub_task(client, token, "d_l3_2", account.id)
    resp2 = client.post(
        "/publish-tasks",
        json={"draft_id": "d_l3_2", "account_id": account.id, "platform": "xhs", "task_hub_task_id": hub2},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp2.status_code == 201
    data2 = resp2.json()
    assert data2["status"] == "skipped"
    assert data2["publish_skipped_reason"]
    assert "limit" in data2["publish_skipped_reason"].lower() or "reached" in data2["publish_skipped_reason"].lower()


# ─── Staggered Scheduling ───


def test_scheduler_enforces_daily_limit():
    """Red: Scheduler should reject if account exceeds daily publish limit."""
    from src.services.publish_scheduler import schedule_publish, clear_schedule_log

    clear_schedule_log()

    # Schedule up to default mature limit (5)
    for i in range(5):
        result = schedule_publish(draft_id=f"d{i}", account_id="acc_limit", platform="xhs")
        assert result["success"] is True, f"Failed at iteration {i}"

    # 6th should fail (default daily limit = 5 for unknown accounts)
    result = schedule_publish(draft_id="d_overflow", account_id="acc_limit", platform="xhs")
    assert result["success"] is False
    assert "limit" in result["reason"].lower() or "上限" in result["reason"]


def test_scheduler_assigns_time_slots():
    """Red: Scheduler should assign non-overlapping time slots."""
    from src.services.publish_scheduler import schedule_publish, clear_schedule_log

    clear_schedule_log()

    result1 = schedule_publish(draft_id="d1", account_id="acc_slot", platform="xhs")
    result2 = schedule_publish(draft_id="d2", account_id="acc_slot", platform="xhs")

    assert result1["success"] is True
    assert result2["success"] is True
    # Two tasks for same account should have different scheduled_at
    assert result1["scheduled_at"] != result2["scheduled_at"]


# ─── Frequency Ladder ───


def test_frequency_ladder_cold_start():
    """Red: cold_start account should have daily limit = 1."""
    from src.models.account_pool import clear_pool_entries, create_pool_entry
    from src.services.publish_scheduler import schedule_publish, clear_schedule_log

    clear_pool_entries()
    clear_schedule_log()

    account = create_pool_entry(
        platform="xhs",
        account_id="freq_cold_001",
        nickname="Test",
        cookie="mock_cookie",
        persona="cat",
        content_vertical="health",
        lifecycle_phase="cold_start",
        fingerprint_profile={
            "user_agent": "ua",
            "viewport": {"width": 1280, "height": 720},
            "locale": "zh-CN",
            "timezone": "Asia/Shanghai",
        },
    )

    result1 = schedule_publish(draft_id="f1", account_id=account.id, platform="xhs")
    assert result1["success"] is True
    result2 = schedule_publish(draft_id="f2", account_id=account.id, platform="xhs")
    assert result2["success"] is False
    assert "limit" in result2["reason"].lower()


# ─── Playwright Publishing (MVP Mock) ───


def test_publish_execution_mock(client):
    """Red Playwright publisher should execute publish and return result."""
    from unittest.mock import MagicMock, patch

    from src.services.playwright_publisher import publish_content

    with patch("src.services.xhs_publisher._get_xhs_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.create_image_note.return_value = {"note_id": "mock_note_123"}
        mock_get_client.return_value = mock_client

        result = publish_content(
            draft_id="draft_test",
            account_id="acc_test",
            platform="xhs",
            content={"title": "测试", "body": "内容", "tags": ["测试"]},
        )
        assert result["success"] is True
        assert "published_url" in result or "platform_post_id" in result
        assert result.get("platform") == "xhs"


def test_publish_tracks_failure():
    """Red: Failed publish should record error reason."""
    from src.services.playwright_publisher import publish_content

    # Simulate failure with invalid platform
    result = publish_content(
        draft_id="draft_fail",
        account_id="acc_fail",
        platform="invalid_platform",
        content={"title": "", "body": "", "tags": []},
    )
    assert result["success"] is False
    assert "error" in result or "reason" in result


# ─── Data Isolation (Phase 2) ───


def get_auth_token_and_id(client, role: str = "operator"):
    import uuid
    email = f"test_{uuid.uuid4().hex[:8]}@ecodream.com"
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"testuser_{uuid.uuid4().hex[:8]}",
        "role": role,
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    token = response.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    return token, me.json()["id"]


def test_list_publish_tasks_isolated_by_user(client):
    """用户只能看到自己创建的发布任务。"""
    from src.models.publish_task import clear_tasks
    from src.services.publish_scheduler import clear_schedule_log

    clear_tasks()
    clear_schedule_log()

    token_a, user_a = get_auth_token_and_id(client)
    token_b, user_b = get_auth_token_and_id(client)

    # 直接通过内存模型创建两个用户的发布任务（绕过 API，模拟历史数据）
    from src.models.publish_task import create_task as _create_publish_task
    _create_publish_task("d_a", "a1", "xhs", created_by=user_a)
    _create_publish_task("d_b", "a2", "xhs", created_by=user_b)

    res_a = client.get("/publish-tasks", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a.status_code == 200
    data_a = res_a.json()
    assert data_a["total"] == 1
    assert data_a["tasks"][0]["draft_id"] == "d_a"

    res_b = client.get("/publish-tasks", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["total"] == 1
    assert data_b["tasks"][0]["draft_id"] == "d_b"


def test_get_publish_task_forbidden_for_other_user(client):
    """用户不能查看其他用户的发布任务详情。"""
    from src.models.publish_task import clear_tasks
    clear_tasks()

    token_a, user_a = get_auth_token_and_id(client)
    token_b, user_b = get_auth_token_and_id(client)

    from src.models.publish_task import create_task as _create_publish_task
    pt = _create_publish_task("d_a", "a1", "xhs", created_by=user_a)

    res = client.get(f"/publish-tasks/{pt.id}", headers={"Authorization": f"Bearer {token_b}"})
    assert res.status_code == 403


def test_update_publish_task_forbidden_for_other_user(client):
    """用户不能修改其他用户的发布任务。"""
    from src.models.publish_task import clear_tasks
    clear_tasks()

    token_a, user_a = get_auth_token_and_id(client)
    token_b, user_b = get_auth_token_and_id(client)

    from src.models.publish_task import create_task as _create_publish_task
    pt = _create_publish_task("d_a", "a1", "xhs", created_by=user_a)

    res = client.patch(
        f"/publish-tasks/{pt.id}",
        json={"status": "cancelled"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res.status_code == 403


def test_delete_publish_task_forbidden_for_other_user(client):
    """用户不能删除其他用户的发布任务。"""
    from src.models.publish_task import clear_tasks
    clear_tasks()

    token_a, user_a = get_auth_token_and_id(client)
    token_b, user_b = get_auth_token_and_id(client)

    from src.models.publish_task import create_task as _create_publish_task
    pt = _create_publish_task("d_a", "a1", "xhs", created_by=user_a)

    res = client.delete(f"/publish-tasks/{pt.id}", headers={"Authorization": f"Bearer {token_b}"})
    assert res.status_code == 403


def test_execute_publish_task_forbidden_for_other_user(client):
    """用户不能执行其他用户的发布任务。"""
    from src.models.publish_task import clear_tasks
    clear_tasks()

    token_a, user_a = get_auth_token_and_id(client)
    token_b, user_b = get_auth_token_and_id(client)

    from src.models.publish_task import create_task as _create_publish_task
    pt = _create_publish_task("d_a", "a1", "xhs", created_by=user_a)

    res = client.post(
        f"/publish-tasks/{pt.id}/execute",
        json={"content": {"title": "T", "body": "B", "tags": []}},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res.status_code == 403
