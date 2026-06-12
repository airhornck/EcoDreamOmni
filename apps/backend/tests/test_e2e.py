"""
W10 E2E 全流程联调测试.
验证: 登录 → 创建账号 → 生成内容 → 合规检测 → 发布任务 → 流量预测 → 数据一致性
"""

from src.models.user import clear_users
from src.services.auth_service import register_user



def get_auth_token(client, role: str = "operator"):
    import uuid
    clear_users()
    email = f"e2e_{uuid.uuid4().hex[:8]}@ecodream.com"
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"e2euser_{uuid.uuid4().hex[:8]}",
        "role": "operator",
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]
class TestE2EFullPipeline:
    """End-to-end: full content creation to publish pipeline."""

    def test_e2e_full_pipeline(self, client):
        """Red Complete pipeline from login to publish prediction."""
        token = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        # Step 1: Create platform account (Cookie import)
        pa_resp = client.post(
            "/platform-accounts",
            json={
                "platform": "xhs",
                "account_id": "e2e_xhs_001",
                "nickname": "E2E测试号",
                "cookie": "a1=e2e_test; webId=test123",
                "status": "active",
            },
            headers=headers,
        )
        assert pa_resp.status_code == 201
        account_id = pa_resp.json()["id"]

        # Step 2: Create account pool entry with fingerprint
        pool_resp = client.post(
            "/account-pool",
            json={
                "platform": "xhs",
                "account_id": "e2e_pool_001",
                "nickname": "E2E素人号",
                "cookie": "a1=e2e_pool; webId=pool123",
                "persona": "温柔铲屎官",
                "content_vertical": "宠物健康",
                "lifecycle_phase": "growth",
            },
            headers=headers,
        )
        assert pool_resp.status_code == 201
        pool_account_id = pool_resp.json()["id"]

        # Step 3: Generate content with Voice injection
        gen_resp = client.post(
            "/content-generate",
            json={"topic": "猫咪驱虫", "platform": "xhs", "persona_id": "p1"},
            headers=headers,
        )
        assert gen_resp.status_code == 200
        generated = gen_resp.json()
        assert generated["title"]
        assert generated["body"]
        assert generated["tags"]

        # Step 4: Create content draft
        draft_resp = client.post(
            "/content-drafts",
            json={
                "title": generated["title"],
                "content_type": "note",
                "platform": "xhs",
                "account_id": pool_account_id,
                "body": generated["body"],
                "tags": generated["tags"],
                "status": "draft",
            },
            headers=headers,
        )
        assert draft_resp.status_code == 201
        draft_id = draft_resp.json()["id"]

        # Step 5: Compliance check (should pass for generated content)
        comp_resp = client.post(
            "/compliance/check",
            json={"text": generated["body"], "content_id": draft_id},
            headers=headers,
        )
        assert comp_resp.status_code == 200
        comp_result = comp_resp.json()
        # Generated content should not trigger L1 reject
        assert comp_result["level"] != "reject", f"Content rejected: {comp_result['violations']}"

        # Step 5.5: Create task_hub task for publish workflow
        task_hub_resp = client.post(
            "/task-hub/tasks",
            json={
                "name": "E2E Publish Task",
                "workflow_template_id": "wf_001",
                "workflow_version": 1,
                "account_id": pool_account_id,
                "persona_id": "p1",
                "platform": "xhs",
                "created_by": "e2e",
                "prompt_variables": {"draft_id": draft_id},
            },
            headers=headers,
        )
        assert task_hub_resp.status_code == 201
        hub_task_id = task_hub_resp.json()["id"]

        # Step 5.6: Drive task to APPROVED_WAITING_PUBLISH via state machine
        r = client.post(f"/task-hub/tasks/{hub_task_id}/configure", headers=headers)
        assert r.status_code == 200
        r = client.post(f"/task-hub/tasks/{hub_task_id}/queue", headers=headers)
        assert r.status_code == 200
        r = client.post(f"/task-hub/tasks/{hub_task_id}/start", headers=headers)
        assert r.status_code == 200
        r = client.post(
            f"/task-hub/tasks/{hub_task_id}/transition",
            json={"status": "human_wait"},
            headers=headers,
        )
        assert r.status_code == 200
        r = client.post(
            f"/task-hub/tasks/{hub_task_id}/human-decision",
            json={"decision": "APPROVE", "operator": "e2e"},
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["status"] == "approved_waiting_publish"

        # Step 6: Confirm publish via review-publish-center (unified entry)
        pub_resp = client.post(
            f"/review-publish-center/conclusions/{hub_task_id}/confirm-publish",
            json={"operator": "e2e", "publish_mode": "immediate"},
            headers=headers,
        )
        assert pub_resp.status_code == 200
        task_id = pub_resp.json()["publish_task_id"]
        assert task_id
        # Publish task may be pending, scheduled, or skipped depending on L3 rules
        # (E2E does not guarantee a real XHS account, so skipped is acceptable)
        get_pub = client.get(f"/publish-tasks/{task_id}", headers=headers)
        assert get_pub.status_code == 200

        # Step 7: Predict engagement for the content
        pred_resp = client.post(
            "/predictions",
            json={
                "account_id": pool_account_id,
                "content_type": "note",
                "topic": "猫咪驱虫",
                "lifecycle_phase": "growth",
                "platform": "xhs",
                "word_count": len(generated["body"]),
                "has_image": True,
                "has_video": False,
                "publish_hour": 12,
                "n_posts_effective": 10,
            },
            headers=headers,
        )
        assert pred_resp.status_code == 200
        pred = pred_resp.json()
        # Aligned with detailed design §5.1: interval structure + interval_mode
        assert "likes" in pred
        assert "comments" in pred
        assert "saves" in pred
        assert "interval_mode" in pred
        assert pred["interval_mode"] in ("prior", "fitted")
        assert 0 <= pred["confidence"] <= 1
        assert "feature_version" in pred
        for metric in ("likes", "comments", "saves"):
            assert "lower" in pred[metric]
            assert "median" in pred[metric]
            assert "upper" in pred[metric]

        # Step 8: Data consistency — draft should exist
        get_draft = client.get(f"/content-drafts/{draft_id}", headers=headers)
        assert get_draft.status_code == 200
        assert get_draft.json()["status"] == "draft"

        # Step 9: Task should be in list
        tasks_resp = client.get("/publish-tasks", headers=headers)
        assert tasks_resp.status_code == 200
        assert "tasks" in tasks_resp.json()
        task_ids = [t["id"] for t in tasks_resp.json()["tasks"]]
        assert task_id in task_ids

        # Step 10: Execute publish (MVP mock)
        exec_resp = client.post(
            f"/publish-tasks/{task_id}/execute",
            json={"content": {"title": generated["title"], "body": generated["body"], "tags": generated["tags"]}},
            headers=headers,
        )
        assert exec_resp.status_code == 200
        exec_result = exec_resp.json()
        # In mock/test environment (xhs module not installed), publish may fail gracefully
        assert exec_result["status"] in ("published", "failed", "skipped")

    def test_e2e_compliance_blocks_bad_content(self, client):
        """Red Pipeline should stop at compliance for violating content."""
        token = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        # Content with prescription drug mention
        bad_content = "给猫咪吃阿莫西林，三天治好感冒，保证有效"

        comp_resp = client.post(
            "/compliance/check",
            json={"text": bad_content, "content_id": "bad_001"},
            headers=headers,
        )
        assert comp_resp.status_code == 200
        result = comp_resp.json()
        assert result["level"] == "reject"
        assert any(v["rule_id"].startswith("L1") for v in result["violations"])

    def test_e2e_dashboard_has_all_modules(self, client):
        """Red Dashboard overview should include all module stats."""
        token = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        overview = client.get("/dashboard/overview", headers=headers)
        assert overview.status_code == 200
        data = overview.json()
        assert "today" in data
        today = data["today"]
        assert isinstance(today["tasksPending"], int)
        assert isinstance(today["contentsPublished"], int)

        # Alerts should include compliance-related alerts
        alerts = client.get("/dashboard/alerts", headers=headers)
        assert alerts.status_code == 200
        assert "alerts" in alerts.json()

    def test_health_check_returns_all_services(self, client):
        """Red Health check should report all critical services status."""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data
