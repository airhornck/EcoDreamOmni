"""
W16-1 CommentHub 合规版 Red-Green 测试。

核心合规要求:
- 自动评论代码层彻底移除（验证不存在自动发布入口）
- 回复接口强制人工确认
- 诱导话术自动拦截
- 每日回复频率 ≤ 20 条/账号
- jieba 情感分析
"""

from src.models.user import clear_users
from src.services.comment_hub import clear_comment_hub



def get_auth_token(client, role: str = "operator"):
    import uuid
    clear_users()
    clear_comment_hub()
    email = f"comment_{uuid.uuid4().hex[:8]}@ecodream.com"
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"commentuser_{uuid.uuid4().hex[:8]}",
        "role": role,
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]
# =============================================================================
# COMMENT-1: AI建议回复
# =============================================================================


def test_suggest_reply_for_comment(client):
    """🔴 AI能为评论生成回复建议."""
    token = get_auth_token(client)
    response = client.post(
        "/comments/content_001/replies/suggest",
        json={
            "account_id": "acc_xhs_001",
            "original_comment": "我家猫最近总吐毛球，怎么办呀？",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert "reply_id" in data
    assert "suggested_reply" in data
    assert len(data["suggested_reply"]) > 0
    assert data["status"] == "suggested"


def test_suggest_reply_sentiment_analysis(client):
    """🔴 回复建议包含情感分析标签."""
    token = get_auth_token(client)
    response = client.post(
        "/comments/content_002/replies/suggest",
        json={
            "account_id": "acc_xhs_001",
            "original_comment": "太感谢了！用了你的方法猫咪好转了很多！",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    data = response.json()
    assert "sentiment" in data
    assert data["sentiment"] in ["positive", "neutral", "negative"]


# =============================================================================
# COMMENT-2: 诱导话术拦截
# =============================================================================


def test_suggest_reply_blocks_inducement(client):
    """🔴 检测到诱导话术时，建议回复被标记为高风险."""
    token = get_auth_token(client)
    response = client.post(
        "/comments/content_003/replies/suggest",
        json={
            "account_id": "acc_xhs_001",
            "original_comment": "加我微信领免费驱虫药，私聊发地址",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] == "HIGH"
    assert "inducement_detected" in data
    assert data["inducement_detected"] is True
    assert "blocked_keywords" in data


# =============================================================================
# COMMENT-3: 回复强制人工确认
# =============================================================================


def test_submit_reply_requires_review(client):
    """🔴 提交回复后状态为 PENDING_REVIEW."""
    token = get_auth_token(client)
    # 先获取建议
    suggest_resp = client.post(
        "/comments/content_004/replies/suggest",
        json={"account_id": "acc_xhs_001", "original_comment": "请问驱虫药怎么用？"},
        headers={"Authorization": f"Bearer {token}"},
    )
    reply_id = suggest_resp.json()["reply_id"]

    # 提交回复
    response = client.post(
        f"/comments/replies/{reply_id}/submit",
        json={"final_reply": "建议每月一次体外驱虫，具体请遵医嘱~"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PENDING_REVIEW"


def test_reply_cannot_publish_without_approval(client):
    """🔴 未审核通过的回复不能标记为已发布."""
    token = get_auth_token(client)
    suggest_resp = client.post(
        "/comments/content_005/replies/suggest",
        json={"account_id": "acc_xhs_001", "original_comment": "谢谢分享！"},
        headers={"Authorization": f"Bearer {token}"},
    )
    reply_id = suggest_resp.json()["reply_id"]

    # 尝试直接发布（不存在此接口）
    response = client.post(
        f"/comments/replies/{reply_id}/publish",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404  # 接口不存在


def test_approve_reply_changes_status(client):
    """🔴 审核通过后状态变为 APPROVED."""
    token = get_auth_token(client, "reviewer")
    suggest_resp = client.post(
        "/comments/content_006/replies/suggest",
        json={"account_id": "acc_xhs_001", "original_comment": "很有帮助！"},
        headers={"Authorization": f"Bearer {token}"},
    )
    reply_id = suggest_resp.json()["reply_id"]

    # 提交
    client.post(
        f"/comments/replies/{reply_id}/submit",
        json={"final_reply": "谢谢支持！"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # 审核通过
    response = client.post(
        f"/comments/replies/{reply_id}/approve",
        json={"reviewer_id": "reviewer_001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "APPROVED"
    assert data["reviewed_by"] == "reviewer_001"


def test_reject_reply_changes_status(client):
    """🔴 审核拒绝后状态变为 REJECTED."""
    token = get_auth_token(client, "reviewer")
    suggest_resp = client.post(
        "/comments/content_007/replies/suggest",
        json={"account_id": "acc_xhs_001", "original_comment": "test"},
        headers={"Authorization": f"Bearer {token}"},
    )
    reply_id = suggest_resp.json()["reply_id"]

    client.post(
        f"/comments/replies/{reply_id}/submit",
        json={"final_reply": "test reply"},
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.post(
        f"/comments/replies/{reply_id}/reject",
        json={"reviewer_id": "reviewer_001", "reason": "包含未核实信息"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "REJECTED"
    assert data["reject_reason"] == "包含未核实信息"


# =============================================================================
# COMMENT-4: 每日回复频率限制
# =============================================================================


def test_daily_reply_limit_20_per_account(client):
    """🔴 每个账号每日回复不超过20条."""
    token = get_auth_token(client)
    account_id = "acc_xhs_limit"

    # 创建21条回复建议并全部审核通过
    for i in range(21):
        suggest_resp = client.post(
            "/comments/content_limit/replies/suggest",
            json={"account_id": account_id, "original_comment": f"comment {i}"},
            headers={"Authorization": f"Bearer {token}"},
        )
        reply_id = suggest_resp.json()["reply_id"]
        client.post(
            f"/comments/replies/{reply_id}/submit",
            json={"final_reply": f"reply {i}"},
            headers={"Authorization": f"Bearer {token}"},
        )
        client.post(
            f"/comments/replies/{reply_id}/approve",
            json={"reviewer_id": "reviewer_001"},
            headers={"Authorization": f"Bearer {token}"},
        )

    # 检查统计
    stats_resp = client.get(
        f"/comments/account/{account_id}/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["daily_published_count"] <= 20


# =============================================================================
# COMMENT-5: 自动评论入口不存在
# =============================================================================


def test_auto_publish_endpoint_does_not_exist(client):
    """🔴 自动发布评论的接口不存在（代码层验证）."""
    token = get_auth_token(client)
    # 尝试调用各种可能的自动评论接口
    auto_endpoints = [
        "/comments/auto-reply",
        "/comments/auto-publish",
        "/comments/batch-auto",
        "/comments/robot-reply",
    ]
    for endpoint in auto_endpoints:
        response = client.post(endpoint, json={}, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 404, f"Endpoint {endpoint} should not exist"


# =============================================================================
# COMMENT-6: 待审核列表
# =============================================================================


def test_list_pending_replies(client):
    """🔴 能获取待审核回复列表."""
    token = get_auth_token(client, "reviewer")
    for i in range(3):
        suggest_resp = client.post(
            "/comments/content_pending/replies/suggest",
            json={"account_id": "acc_xhs_001", "original_comment": f"pending {i}"},
            headers={"Authorization": f"Bearer {token}"},
        )
        reply_id = suggest_resp.json()["reply_id"]
        client.post(
            f"/comments/replies/{reply_id}/submit",
            json={"final_reply": f"reply {i}"},
            headers={"Authorization": f"Bearer {token}"},
        )

    response = client.get(
        "/comments/pending-review",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 3
    for item in data["items"]:
        assert item["status"] == "PENDING_REVIEW"
