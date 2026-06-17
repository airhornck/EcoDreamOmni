"""
AssetPool 三源混合素材库 Red-Green 测试。
V2.7.1新增需求: 三源上传、版权校验、AI标识、匹配推荐
"""

from src.models.user import clear_users
from tests.conftest import sync_clear_asset_pool



def get_auth_token(client, role: str = "operator"):
    import uuid
    clear_users()
    sync_clear_asset_pool()
    email = f"asset_{uuid.uuid4().hex[:8]}@ecodream.com"
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"assetuser_{uuid.uuid4().hex[:8]}",
        "role": "operator",
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]
# =============================================================================
# ASSET-1: 三源上传测试 (运营上传/图库API/AI生成)
# =============================================================================

def test_upload_asset_operator(client):
    """🔴 测试: 运营上传素材 (source_type=OPERATOR_UPLOAD)"""
    token = get_auth_token(client)
    response = client.post(
        "/assets/upload",
        json={
            "filename": "cat_nutrition_guide.jpg",
            "file_url": "https://cdn.example.com/cat_nutrition.jpg",
            "source_type": "OPERATOR_UPLOAD",
            "license_type": "OWNED",
            "tags": ["猫咪", "营养", "指南"],
            "category": "nutrition",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert data["id"]
    assert data["source_type"] == "OPERATOR_UPLOAD"
    assert data["license_type"] == "OWNED"
    assert data["status"] == "ACTIVE"


def test_upload_asset_stock_api(client):
    """🔴 测试: 图库API导入素材 (source_type=STOCK_API)"""
    token = get_auth_token(client)
    response = client.post(
        "/assets/upload",
        json={
            "filename": "vet_consultation_stock.jpg",
            "file_url": "https://stock.example.com/vet.jpg",
            "source_type": "STOCK_API",
            "license_type": "LICENSED",
            "stock_source": "shutterstock",
            "stock_id": "ss_12345",
            "license_expiry": "2025-12-31T00:00:00Z",
            "tags": ["兽医", "咨询", "专业"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["source_type"] == "STOCK_API"
    assert data["license_type"] == "LICENSED"
    assert "stock_source" in data


def test_upload_asset_ai_generated(client):
    """🔴 测试: AI生成素材 (source_type=AI_GENERATED)"""
    token = get_auth_token(client)
    response = client.post(
        "/assets/upload",
        json={
            "filename": "ai_cat_food.jpg",
            "file_url": "https://ai-generate.example.com/cat.jpg",
            "source_type": "AI_GENERATED",
            "license_type": "AI_GENERATED",
            "ai_model": "dalle-3",
            "ai_prompt": "cute cat eating healthy food",
            "tags": ["AI生成", "猫咪", "食物"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["source_type"] == "AI_GENERATED"
    # 关键: AI生成图片必须有AI辅助创作标签
    assert data["ai_disclosure"] is True
    assert "AI辅助创作" in data["tags"]


# =============================================================================
# ASSET-2: 版权校验测试
# =============================================================================

def test_asset_copyright_validation(client):
    """🔴 测试: 素材版权信息完整校验"""
    token = get_auth_token(client)
    
    # 创建有完整版权信息的素材
    response = client.post(
        "/assets/upload",
        json={
            "filename": "copyrighted.jpg",
            "file_url": "https://example.com/copyrighted.jpg",
            "source_type": "OPERATOR_UPLOAD",
            "license_type": "OWNED",
            "copyright_holder": "EcoDream Inc",
            "copyright_year": 2024,
            "usage_rights": ["web", "social_media"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["copyright_validated"] is True


def test_asset_license_expiry_check(client):
    """🔴 测试: 图库素材许可证过期检查"""
    token = get_auth_token(client)
    from datetime import datetime, timedelta, timezone
    
    # 创建即将过期的素材
    expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    response = client.post(
        "/assets/upload",
        json={
            "filename": "expiring_soon.jpg",
            "file_url": "https://stock.example.com/expiring.jpg",
            "source_type": "STOCK_API",
            "license_type": "LICENSED",
            "license_expiry": expiry,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["license_status"] == "EXPIRING_SOON"


def test_list_assets_with_license_filter(client):
    """🔴 测试: 按许可证状态筛选素材"""
    token = get_auth_token(client)
    
    # 创建多种素材
    client.post(
        "/assets/upload",
        json={
            "filename": "owned.jpg",
            "file_url": "https://example.com/owned.jpg",
            "source_type": "OPERATOR_UPLOAD",
            "license_type": "OWNED",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    
    # 查询OWNED类型的素材
    response = client.get(
        "/assets?license_type=OWNED",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1
    for item in data["items"]:
        assert item["license_type"] == "OWNED"


# =============================================================================
# ASSET-3: AI标识测试
# =============================================================================

def test_ai_asset_forced_disclosure(client):
    """🔴 测试: AI生成图片强制附加AI辅助创作标签"""
    token = get_auth_token(client)
    
    response = client.post(
        "/assets/upload",
        json={
            "filename": "ai_pet.jpg",
            "file_url": "https://ai.example.com/pet.jpg",
            "source_type": "AI_GENERATED",
            "license_type": "AI_GENERATED",
            "ai_model": "midjourney",
            "tags": ["可爱", "宠物"],  # 未包含AI标签
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    
    # 验证强制添加AI标签
    assert data["ai_disclosure"] is True
    assert "AI辅助创作" in data["tags"]
    # 验证元数据包含AI信息
    assert data["ai_metadata"]["model"] == "midjourney"
    assert "prompt" in data["ai_metadata"]


def test_ai_asset_cannot_remove_disclosure(client):
    """🔴 测试: 无法手动移除AI标识"""
    token = get_auth_token(client)
    
    # 创建AI素材
    create_resp = client.post(
        "/assets/upload",
        json={
            "filename": "ai_test.jpg",
            "file_url": "https://ai.example.com/test.jpg",
            "source_type": "AI_GENERATED",
            "license_type": "AI_GENERATED",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    asset_id = create_resp.json()["id"]
    
    # 尝试移除AI标签
    response = client.patch(
        f"/assets/{asset_id}",
        json={
            "tags": ["宠物"],  # 不包含AI标签
            "ai_disclosure": False,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    
    # 应该被拒绝或强制保留AI标签
    if response.status_code == 200:
        data = response.json()
        assert data["ai_disclosure"] is True
        assert "AI辅助创作" in data["tags"]


# =============================================================================
# ASSET-4: 素材匹配推荐测试
# =============================================================================

def test_recommend_assets_for_content(client):
    """🔴 测试: 根据内容推荐匹配素材"""
    token = get_auth_token(client)
    
    # 先上传几个素材
    for i in range(3):
        client.post(
            "/assets/upload",
            json={
                "filename": f"cat_nutrition_{i}.jpg",
                "file_url": f"https://example.com/cat_{i}.jpg",
                "source_type": "OPERATOR_UPLOAD",
                "license_type": "OWNED",
                "tags": ["猫咪", "营养", "健康"],
                "category": "nutrition",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    
    # 请求素材推荐
    response = client.post(
        "/assets/recommend",
        json={
            "content_title": "猫咪营养指南：如何科学喂养",
            "content_body": "科学喂养是保持猫咪健康的关键...",
            "content_tags": ["猫咪", "营养", "喂养"],
            "target_count": 3,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert len(data["recommendations"]) <= 3
    
    # 验证匹配分数
    for rec in data["recommendations"]:
        assert "asset_id" in rec
        assert "match_score" in rec
        assert 0 <= rec["match_score"] <= 100
        assert "match_reason" in rec


def test_asset_match_with_content_series(client):
    """🔴 测试: 系列化内容素材匹配"""
    token = get_auth_token(client)
    
    # 上传系列素材
    client.post(
        "/assets/upload",
        json={
            "filename": "series_part1.jpg",
            "file_url": "https://example.com/series1.jpg",
            "source_type": "OPERATOR_UPLOAD",
            "license_type": "OWNED",
            "tags": ["驱虫", "系列", "第一篇"],
            "series_id": "deworm_series",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    
    # 请求系列内容素材
    response = client.post(
        "/assets/recommend",
        json={
            "content_title": "驱虫指南第二篇",
            "series_id": "deworm_series",
            "content_tags": ["驱虫"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    
    # 验证系列素材优先
    if data["recommendations"]:
        first_rec = data["recommendations"][0]
        assert "series" in first_rec.get("match_reason", "").lower()


# =============================================================================
# ASSET-5: 三源比例统计测试
# =============================================================================

def test_asset_source_ratio_statistics(client):
    """🔴 测试: 统计三源素材比例，确保运营上传>=70%"""
    token = get_auth_token(client)
    
    # 清除现有数据
    sync_clear_asset_pool()
    
    # 创建测试数据: 7个运营上传 + 3个其他来源
    for i in range(7):
        client.post(
            "/assets/upload",
            json={
                "filename": f"op_{i}.jpg",
                "file_url": f"https://op.example.com/{i}.jpg",
                "source_type": "OPERATOR_UPLOAD",
                "license_type": "OWNED",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    
    for i in range(2):
        client.post(
            "/assets/upload",
            json={
                "filename": f"stock_{i}.jpg",
                "file_url": f"https://stock.example.com/{i}.jpg",
                "source_type": "STOCK_API",
                "license_type": "LICENSED",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    
    client.post(
        "/assets/upload",
        json={
            "filename": "ai.jpg",
            "file_url": "https://ai.example.com/1.jpg",
            "source_type": "AI_GENERATED",
            "license_type": "AI_GENERATED",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    
    # 查询统计
    response = client.get(
        "/assets/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    
    assert "source_distribution" in data
    distribution = data["source_distribution"]
    assert "OPERATOR_UPLOAD" in distribution
    assert "STOCK_API" in distribution
    assert "AI_GENERATED" in distribution
    
    # 验证运营上传占比 >= 70%
    total = sum(distribution.values())
    op_ratio = distribution["OPERATOR_UPLOAD"] / total * 100
    assert op_ratio >= 70, f"运营上传占比 {op_ratio}% < 70%"


# =============================================================================
# ASSET-6: 缩略图生成测试
# =============================================================================

def test_asset_thumbnail_generation(client):
    """🔴 测试: 自动生成缩略图"""
    token = get_auth_token(client)
    
    response = client.post(
        "/assets/upload",
        json={
            "filename": "thumbnail_test.jpg",
            "file_url": "https://example.com/large_image.jpg",
            "source_type": "OPERATOR_UPLOAD",
            "license_type": "OWNED",
            "generate_thumbnail": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    
    # 验证缩略图URL生成
    assert "thumbnail_url" in data
    assert data["thumbnail_url"].endswith("_thumb.jpg")


# =============================================================================
# ASSET-7: 素材详情和更新测试
# =============================================================================

def test_get_asset_detail(client):
    """🔴 测试: 获取素材详情"""
    token = get_auth_token(client)
    
    # 创建素材
    create_resp = client.post(
        "/assets/upload",
        json={
            "filename": "detail_test.jpg",
            "file_url": "https://example.com/detail.jpg",
            "source_type": "OPERATOR_UPLOAD",
            "license_type": "OWNED",
            "tags": ["测试", "详情"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    asset_id = create_resp.json()["id"]
    
    # 获取详情
    response = client.get(
        f"/assets/{asset_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == asset_id
    assert data["filename"] == "detail_test.jpg"
    assert "created_at" in data
    assert "updated_at" in data


def test_update_asset_metadata(client):
    """🔴 测试: 更新素材元数据"""
    token = get_auth_token(client)
    
    create_resp = client.post(
        "/assets/upload",
        json={
            "filename": "update_test.jpg",
            "file_url": "https://example.com/update.jpg",
            "source_type": "OPERATOR_UPLOAD",
            "license_type": "OWNED",
            "tags": ["旧标签"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    asset_id = create_resp.json()["id"]
    
    # 更新元数据
    response = client.patch(
        f"/assets/{asset_id}",
        json={
            "tags": ["新标签", "猫咪"],
            "description": "更新后的描述",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "新标签" in data["tags"]
    assert data["description"] == "更新后的描述"


# =============================================================================
# ASSET-8: 素材删除和软删除测试
# =============================================================================

def test_soft_delete_asset(client):
    """🔴 测试: 软删除素材"""
    token = get_auth_token(client)
    
    create_resp = client.post(
        "/assets/upload",
        json={
            "filename": "delete_test.jpg",
            "file_url": "https://example.com/delete.jpg",
            "source_type": "OPERATOR_UPLOAD",
            "license_type": "OWNED",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    asset_id = create_resp.json()["id"]
    
    # 软删除
    response = client.delete(
        f"/assets/{asset_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    
    # 验证素材状态为DELETED
    detail_resp = client.get(
        f"/assets/{asset_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    data = detail_resp.json()
    assert data["status"] == "DELETED"


def test_list_assets_excludes_deleted(client):
    """🔴 测试: 列表不显示已删除素材"""
    token = get_auth_token(client)
    sync_clear_asset_pool()
    
    # 创建素材
    create_resp = client.post(
        "/assets/upload",
        json={
            "filename": "list_test.jpg",
            "file_url": "https://example.com/list.jpg",
            "source_type": "OPERATOR_UPLOAD",
            "license_type": "OWNED",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    asset_id = create_resp.json()["id"]
    
    # 删除
    client.delete(f"/assets/{asset_id}", headers={"Authorization": f"Bearer {token}"})
    
    # 列表查询
    response = client.get(
        "/assets",
        headers={"Authorization": f"Bearer {token}"},
    )
    data = response.json()
    
    # 验证已删除素材不在列表中
    asset_ids = [item["id"] for item in data["items"]]
    assert asset_id not in asset_ids
