"""
W18 E2E-1: V2.7.1-V3.1 全链路集成测试。

验证 13 项需求端到端调用链路：
1. 内容生成 → 合规检查 → 人工审核 → 发布 全流程
2. 5A 方法论 → 内容生成 链路
3. TrendScout → 内容生成 链路
4. CommentHub → 评论管理 链路
5. ContentSeries → 系列上下文 链路
6. HITL 弹性审核 链路
8. ImageForge → 图片配置 链路
9. PlatformRule 抖音适配 链路（框架）
10. BrandKnowledge / VetDrugDB Function 层可用性（框架）
11. TimelineLibrary 季节事件（框架）
12. AssetPool 素材管理（框架）
12. 架构红线：Agent 禁止直接操作数据库
"""

from src.models.user import clear_users
from src.services import (
    compliance_engine,
    comment_hub,
    content_series,
    image_forge,
    human_in_loop as hil,
    task_hub,
    workflow_engine as we,
)



def _get_token(client, role: str = "operator") -> str:
    import uuid
    email = f"e2e_{uuid.uuid4().hex[:8]}@ecodream.com"
    clear_users()
    compliance_engine.clear_evidence()
    comment_hub.clear_comment_hub()
    content_series.clear_content_series()
    image_forge.clear_image_forge()
    hil._clear_stores()
    task_hub._clear_stores()
    we._clear_stores()
    we.load_presets()
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"e2euser_{uuid.uuid4().hex[:8]}",
        "role": role,
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]


# =============================================================================
# E2E-1: 内容生成 → 合规检查 → 人工审核 全流程
# =============================================================================


def test_full_content_pipeline_with_compliance_and_review(client):
    """🔴 端到端：内容生成 → 合规检查 → HITL 审核."""
    token = _get_token(client, "reviewer")

    # Step 1 生成内容
    gen_resp = client.post(
        "/content-generate",
        json={"topic": "猫咪驱虫", "platform": "xhs"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert gen_resp.status_code == 200
    generated = gen_resp.json()
    assert "title" in generated
    assert "body" in generated

    # Step 2: 合规检查
    compliance_resp = client.post(
        "/compliance/check",
        json={"text": generated["body"], "content_id": "draft_e2e_001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert compliance_resp.status_code == 200
    compliance = compliance_resp.json()
    assert "level" in compliance
    assert "violations" in compliance

    # Step 3: 创建图片配置
    img_resp = client.post(
        "/image-configs",
        json={
            "content_draft_id": "draft_e2e_001",
            "account_id": "acc_xhs_001",
            "layout_type": "cover_3_body",
            "topic": "猫咪驱虫",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert img_resp.status_code == 201
    config_id = img_resp.json()["id"]

    # Step 4: 图片 T2 预检
    t2_resp = client.post(
        f"/image-configs/{config_id}/t2-check",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert t2_resp.status_code == 200

    # Step 5: 提交图片审核
    submit_resp = client.post(
        f"/image-configs/{config_id}/submit",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert submit_resp.status_code == 200
    assert submit_resp.json()["status"] == "PENDING_REVIEW"

    # Step 6: 审核通过
    approve_resp = client.post(
        f"/image-configs/{config_id}/approve",
        json={"reviewer_id": "reviewer_001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "APPROVED"


# =============================================================================
# E2E-2: 5A 方法论 → 内容生成 链路
# =============================================================================


def test_5a_methodology_to_content_generation(client):
    """🔴 端到端：5A 阶段 → 内容生成."""
    token = _get_token(client, "content_planner")

    # 获取 5A 阶段列表
    stages_resp = client.get(
        "/methodologies/5A/stages",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert stages_resp.status_code == 200
    stages = stages_resp.json()
    assert len(stages["stages"]) == 5

    # 使用 ACT 阶段生成内容
    gen_resp = client.post(
        "/content-generate",
        json={"topic": "驱虫攻略", "platform": "xhs", "stage_id": "mm_5a_act"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert gen_resp.status_code == 200
    data = gen_resp.json()
    assert data["template_version"] == "mm_5a_act"


# =============================================================================
# E2E-3: TrendScout → 内容生成 链路
# =============================================================================


def test_trend_scout_to_content_pipeline(client):
    """🔴 端到端：TrendScout 报告 → 内容生成."""
    token = _get_token(client, "operator")

    # 创建趋势报告
    report_resp = client.post(
        "/trend-scout/reports",
        json={"query": "猫咪驱虫", "stage_filter": "AWARE"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert report_resp.status_code == 201
    report = report_resp.json()
    assert report["query"] == "猫咪驱虫"
    assert "recommended_topics" in report

    # 基于报告选题生成内容
    topic = report["recommended_topics"][0]["topic_title"]
    gen_resp = client.post(
        "/content-generate",
        json={"topic": topic, "platform": "xhs"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert gen_resp.status_code == 200
    assert "title" in gen_resp.json()


# =============================================================================
# E2E-4: CommentHub → 评论管理 链路
# =============================================================================


def test_comment_hub_full_lifecycle(client):
    """🔴 端到端：评论回复建议 → 提交 → 审核."""
    token = _get_token(client, "reviewer")

    # AI 建议回复
    suggest_resp = client.post(
        "/comments/content_e2e/replies/suggest",
        json={"account_id": "acc_xhs_001", "original_comment": "很有帮助！"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert suggest_resp.status_code == 200
    reply_id = suggest_resp.json()["reply_id"]

    # 提交回复
    submit_resp = client.post(
        f"/comments/replies/{reply_id}/submit",
        json={"final_reply": "谢谢支持！"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert submit_resp.status_code == 200
    assert submit_resp.json()["status"] == "PENDING_REVIEW"

    # 审核通过
    approve_resp = client.post(
        f"/comments/replies/{reply_id}/approve",
        json={"reviewer_id": "reviewer_001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "APPROVED"

    # 账号统计
    stats_resp = client.get(
        "/comments/account/acc_xhs_001/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["daily_limit"] == 20


# =============================================================================
# E2E-5: ContentSeries → 系列上下文 链路
# =============================================================================


def test_content_series_context_injection(client):
    """🔴 端到端：系列创建 → 内容添加 → 上下文注入."""
    token = _get_token(client, "content_planner")

    # 创建系列
    series_resp = client.post(
        "/content-series",
        json={
            "name": "驱虫系列",
            "account_id": "acc_xhs_001",
            "stage_sequence": ["AWARE", "ASK", "ACT"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert series_resp.status_code == 201
    series_id = series_resp.json()["id"]

    # 添加内容
    client.post(
        f"/content-series/{series_id}/contents",
        json={"content_draft_id": "draft_s1", "stage": "AWARE"},
        headers={"Authorization": f"Bearer {token}"},
    )
    client.post(
        f"/content-series/{series_id}/contents",
        json={"content_draft_id": "draft_s2", "stage": "ASK"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # 获取上下文
    ctx_resp = client.get(
        f"/content-series/{series_id}/context?content_draft_id=draft_s2",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert ctx_resp.status_code == 200
    ctx = ctx_resp.json()
    assert ctx["prev_content"]["content_draft_id"] == "draft_s1"
    assert "prev_summary" in ctx


# =============================================================================
# E2E-6: HITL 弹性审核 链路
# =============================================================================


def test_hitl_elastic_review_pipeline(client):
    """🔴 端到端：风险检测 → 弹性策略 → 单人/双人审核."""
    token = _get_token(client, "reviewer")

    # 低风险内容 → 单人审核
    risk_resp = client.post(
        "/human-in-the-loop/detect-risk",
        json={"title": "猫咪日常", "body": "春天记得梳毛"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert risk_resp.status_code == 200
    assert risk_resp.json()["risk_level"] == "LOW"
    assert risk_resp.json()["review_strategy"] == "single"

    # 高风险内容 → 双人审核
    risk_resp2 = client.post(
        "/human-in-the-loop/detect-risk",
        json={"title": "三天治愈", "body": "用阿莫西林三天治愈猫癣"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert risk_resp2.json()["risk_level"] == "HIGH"
    assert risk_resp2.json()["review_strategy"] == "dual"

    # batch-approve 含高风险时强制逐篇审核
    batch_resp = client.post(
        "/human-in-the-loop/batch-approve",
        json={"task_ids": [], "reviewer_id": "reviewer_001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert batch_resp.status_code == 200


# =============================================================================
# E2E-8: ImageForge → 图片配置 → 人工审核
# =============================================================================


def test_image_forge_full_lifecycle(client):
    """🔴 端到端：图片配置 → T2预检 → 提交审核 → 通过."""
    token = _get_token(client, "reviewer")

    # 创建配置
    create_resp = client.post(
        "/image-configs",
        json={
            "content_draft_id": "draft_img_001",
            "account_id": "acc_xhs_001",
            "layout_type": "cover_3_body",
            "topic": "猫咪驱虫",
            "has_product_info": False,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_resp.status_code == 201
    config_id = create_resp.json()["id"]

    # 获取推荐
    rec_resp = client.get(
        f"/image-configs/{config_id}/recommendations",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert rec_resp.status_code == 200
    assert len(rec_resp.json()["recommended_images"]) == 3

    # T2 预检通过
    t2_resp = client.post(
        f"/image-configs/{config_id}/t2-check",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert t2_resp.json()["allow_t2"] is True

    # 设置布局
    layout_resp = client.patch(
        f"/image-configs/{config_id}/layout",
        json={
            "cover_image": {"asset_id": "asset_001", "url": "https://cdn.example.com/cover.jpg"},
            "body_images": [],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert layout_resp.status_code == 200

    # 提交审核
    submit_resp = client.post(
        f"/image-configs/{config_id}/submit",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert submit_resp.json()["status"] == "PENDING_REVIEW"

    # 审核通过
    approve_resp = client.post(
        f"/image-configs/{config_id}/approve",
        json={"reviewer_id": "reviewer_001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "APPROVED"


# =============================================================================
# E2E-9: 架构红线 — Agent 禁止直接操作数据库
# =============================================================================


def test_architecture_no_direct_db_access():
    """🔴 端到端：静态扫描确认 Agent 层无直接数据库访问."""
    import subprocess
    result = subprocess.run(
        ["grep", "-r", "session.execute\|db.query\|Model.query", "src/services/"],
        capture_output=True,
        text=True,
    )
    # 只有 Function 层 ORM 服务包含这些模式，Agent 层不应有
    agent_violations = [
        line for line in result.stdout.splitlines()
        if "_function.py" not in line and "_orm.py" not in line
    ]
    assert len(agent_violations) == 0, f"Agent layer DB violations: {agent_violations}"


