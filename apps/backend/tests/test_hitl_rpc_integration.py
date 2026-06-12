"""
HITL 合并到 RPC 集成测试。

验证：
  - RPC conclusions pending filter 正确返回 HUMAN_WAIT 任务
  - 通过 HITL API 操作后，RPC conclusions 实时反映状态变化
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.services import task_hub as th
from src.services import human_in_loop as hil


def get_auth_token(client):
    import uuid
    from src.models.user import clear_users
    from src.services.auth_service import register_user
    clear_users()
    th._clear_stores()
    hil._clear_stores()
    email = f"hitl_rpc_{uuid.uuid4().hex[:8]}@ecodream.com"
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"hitluser_{uuid.uuid4().hex[:8]}",
        "role": "operator",
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    token = response.json()["access_token"]
    me_resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    user_id = me_resp.json()["id"]
    return token, user_id


async def _create_human_wait_task(db, created_by, name="HITL Task", wf="wf_001"):
    """Helper: 创建并推进到 HUMAN_WAIT 状态的任务。"""
    t = await th.create_task(db, name, wf, 1, "acc_1", "pers_1", created_by=created_by)
    await th.configure(db, t.id)
    await th.queue(db, t.id)
    await th.start(db, t.id)
    await th.wait_human(db, t.id)
    return t


class TestHitlRpcIntegration:
    """🔴 HITL 合并到 RPC 的集成测试。"""

    async def test_pending_tasks_appear_in_rpc(self, client, db):
        """HUMAN_WAIT 任务出现在 RPC conclusions 的 pending filter 中。"""
        token, user_id = get_auth_token(client)
        t = await _create_human_wait_task(db, created_by=user_id)

        response = client.get(
            "/review-publish-center/conclusions?status_filter=pending",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["task_id"] == t.id
        assert data["items"][0]["status"] == "human_wait"

    async def test_approve_moves_task_from_pending_to_approved(self, client, db):
        """approve 后任务从 pending 消失，出现在 approved。"""
        token, user_id = get_auth_token(client)
        t = await _create_human_wait_task(db, created_by=user_id)

        # Approve via HITL API
        res = client.post(
            f"/human-in-the-loop/tasks/{t.id}/approve",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200

        # Pending should be empty
        response = client.get(
            "/review-publish-center/conclusions?status_filter=pending",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.json()["total"] == 0

        # Approved should contain the task
        response = client.get(
            "/review-publish-center/conclusions?status_filter=approved",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["task_id"] == t.id
        assert data["items"][0]["review_decision"] == "APPROVE"

    async def test_reject_task_in_rpc(self, client, db):
        """reject 后任务从 pending 消失，出现在 rejected。"""
        token, user_id = get_auth_token(client)
        t = await _create_human_wait_task(db, created_by=user_id)

        res = client.post(
            f"/human-in-the-loop/tasks/{t.id}/reject",
            json={"operator": "reviewer_1", "reason": "违规内容"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200

        response = client.get(
            "/review-publish-center/conclusions?status_filter=pending",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.json()["total"] == 0

        response = client.get(
            "/review-publish-center/conclusions?status_filter=rejected",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["task_id"] == t.id
        assert data["items"][0]["review_decision"] == "REJECT"
        assert data["items"][0]["review_reason"] == "违规内容"

    async def test_revise_task_in_rpc(self, client, db):
        """revise 后任务从 pending 消失。"""
        token, user_id = get_auth_token(client)
        t = await _create_human_wait_task(db, created_by=user_id)

        res = client.post(
            f"/human-in-the-loop/tasks/{t.id}/revise",
            json={"operator": "reviewer_1", "reason": "需要修改标题"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200

        response = client.get(
            "/review-publish-center/conclusions?status_filter=pending",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.json()["total"] == 0

        # Task should be in revised filter
        response = client.get(
            "/review-publish-center/conclusions?status_filter=revised",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["task_id"] == t.id
        assert data["items"][0]["review_decision"] == "REVISE"

    async def test_rpc_all_tab_includes_human_wait(self, client, db):
        """all filter 同时包含 HUMAN_WAIT 和已审核的任务。"""
        token, user_id = get_auth_token(client)
        t1 = await _create_human_wait_task(db, created_by=user_id, name="Task A")
        t2 = await _create_human_wait_task(db, created_by=user_id, name="Task B")
        await hil.approve_task(db, t2.id, user_id)

        response = client.get(
            "/review-publish-center/conclusions?status_filter=all",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["total"] == 2
        statuses = {item["status"] for item in data["items"]}
        assert "human_wait" in statuses

    async def test_pending_filter_excludes_non_human_wait(self, client, db):
        """pending filter 不返回非 HUMAN_WAIT 状态的任务。"""
        token, user_id = get_auth_token(client)
        t = await _create_human_wait_task(db, created_by=user_id)
        await hil.approve_task(db, t.id, user_id)

        response = client.get(
            "/review-publish-center/conclusions?status_filter=pending",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.json()["total"] == 0
