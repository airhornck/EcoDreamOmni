"""
W16 IMAGE-1 ImageForge 图片配置引擎 Red-Green 测试。

核心要求:
- 调用 AssetPool 推荐接口获取候选素材
- 排版配置（封面+正文配图）
- 人工干预闭环
- 含产品信息禁止路由 T2 境外模型
- 强制经过人工审核
"""

from src.models.user import clear_users
from src.services.image_forge import clear_image_forge



def get_auth_token(client, role: str = "operator"):
    import uuid
    clear_users()
    clear_image_forge()
    email = f"image_{uuid.uuid4().hex[:8]}@ecodream.com"
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"imageuser_{uuid.uuid4().hex[:8]}",
        "role": role,
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]
# =============================================================================
# IMAGE-1: 图片配置创建
# =============================================================================


def test_create_image_config(client):
    """🔴 能为内容草稿创建图片配置."""
    token = get_auth_token(client)
    response = client.post(
        "/image-configs",
        json={
            "content_draft_id": "draft_001",
            "account_id": "acc_xhs_001",
            "layout_type": "cover_3_body",
            "topic": "猫咪驱虫",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert data["content_draft_id"] == "draft_001"
    assert data["layout_type"] == "cover_3_body"
    assert data["status"] == "draft"
    assert "id" in data


# =============================================================================
# IMAGE-2: AssetPool 素材推荐
# =============================================================================


def test_recommend_images_for_content(client):
    """🔴 能根据内容主题推荐素材图片."""
    token = get_auth_token(client)
    create_resp = client.post(
        "/image-configs",
        json={
            "content_draft_id": "draft_002",
            "account_id": "acc_xhs_001",
            "layout_type": "cover_3_body",
            "topic": "猫咪驱虫",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    config_id = create_resp.json()["id"]

    response = client.get(
        f"/image-configs/{config_id}/recommendations",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert "recommended_images" in data
    # 返回推荐图片列表
    assert isinstance(data["recommended_images"], list)


# =============================================================================
# IMAGE-3: 排版配置
# =============================================================================


def test_set_image_layout(client):
    """🔴 能设置封面和正文配图."""
    token = get_auth_token(client)
    create_resp = client.post(
        "/image-configs",
        json={
            "content_draft_id": "draft_003",
            "account_id": "acc_xhs_001",
            "layout_type": "cover_3_body",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    config_id = create_resp.json()["id"]

    response = client.patch(
        f"/image-configs/{config_id}/layout",
        json={
            "cover_image": {"asset_id": "asset_001", "url": "https://cdn.example.com/cover.jpg"},
            "body_images": [
                {"asset_id": "asset_002", "url": "https://cdn.example.com/body1.jpg"},
                {"asset_id": "asset_003", "url": "https://cdn.example.com/body2.jpg"},
            ],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["cover_image"]["asset_id"] == "asset_001"
    assert len(data["body_images"]) == 2


# =============================================================================
# IMAGE-4: T2 预检 — 含产品信息禁止路由境外模型
# =============================================================================


def test_t2_check_blocks_foreign_model_for_product_content(client):
    """🔴 含产品信息的图片配置禁止路由到T2境外模型."""
    token = get_auth_token(client)
    response = client.post(
        "/image-configs",
        json={
            "content_draft_id": "draft_004",
            "account_id": "acc_xhs_001",
            "layout_type": "cover_3_body",
            "topic": "宠安宁驱虫滴剂",
            "has_product_info": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    config_id = response.json()["id"]

    # T2 预检
    t2_resp = client.post(
        f"/image-configs/{config_id}/t2-check",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert t2_resp.status_code == 200
    data = t2_resp.json()
    assert data["allow_t2"] is False
    assert "product_info_detected" in data
    assert data["reason"] == "含产品信息禁止路由T2境外模型"


def test_t2_check_allows_safe_content(client):
    """🔴 不含产品信息的图片配置允许正常处理."""
    token = get_auth_token(client)
    response = client.post(
        "/image-configs",
        json={
            "content_draft_id": "draft_005",
            "account_id": "acc_xhs_001",
            "layout_type": "cover_3_body",
            "topic": "猫咪日常",
            "has_product_info": False,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    config_id = response.json()["id"]

    t2_resp = client.post(
        f"/image-configs/{config_id}/t2-check",
        headers={"Authorization": f"Bearer {token}"},
    )
    data = t2_resp.json()
    assert data["allow_t2"] is True


# =============================================================================
# IMAGE-5: 强制人工审核
# =============================================================================


def test_image_config_requires_human_approval(client):
    """🔴 图片配置必须经过人工审核才能发布."""
    token = get_auth_token(client)
    create_resp = client.post(
        "/image-configs",
        json={
            "content_draft_id": "draft_006",
            "account_id": "acc_xhs_001",
            "layout_type": "cover_3_body",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    config_id = create_resp.json()["id"]

    # 设置布局
    client.patch(
        f"/image-configs/{config_id}/layout",
        json={
            "cover_image": {"asset_id": "asset_001", "url": "https://cdn.example.com/cover.jpg"},
            "body_images": [],
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    # 提交审核
    submit_resp = client.post(
        f"/image-configs/{config_id}/submit",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert submit_resp.status_code == 200
    assert submit_resp.json()["status"] == "PENDING_REVIEW"

    # 直接发布应该被拒绝（不存在接口）
    publish_resp = client.post(
        f"/image-configs/{config_id}/publish",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert publish_resp.status_code == 404

    # 审核通过
    approve_resp = client.post(
        f"/image-configs/{config_id}/approve",
        json={"reviewer_id": "reviewer_001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "APPROVED"


def test_reject_image_config(client):
    """🔴 人工审核可以拒绝图片配置."""
    token = get_auth_token(client)
    create_resp = client.post(
        "/image-configs",
        json={
            "content_draft_id": "draft_007",
            "account_id": "acc_xhs_001",
            "layout_type": "cover_3_body",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    config_id = create_resp.json()["id"]

    client.post(
        f"/image-configs/{config_id}/submit",
        headers={"Authorization": f"Bearer {token}"},
    )

    reject_resp = client.post(
        f"/image-configs/{config_id}/reject",
        json={"reviewer_id": "reviewer_001", "reason": "版权问题"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert reject_resp.status_code == 200
    data = reject_resp.json()
    assert data["status"] == "REJECTED"
    assert data["reject_reason"] == "版权问题"
