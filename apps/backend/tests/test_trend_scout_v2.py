"""
TrendScout V2.7.1 增强版 Red-Green 测试。
V2.7.1新增需求: 选题报告生成 (PDF/5A匹配度/人群契合度/批量报告)
"""

from src.models.user import clear_users
from src.services.auth_service import register_user
from src.services import trend_scout_v2_service
from src.services.trend_scout_service import clear_trend_scout



def get_auth_token(client, role: str = "operator"):
    import uuid
    clear_users()
    clear_trend_scout()
    trend_scout_v2_service.clear_trend_scout_v2()
    email = f"trend_v2_{uuid.uuid4().hex[:8]}@ecodream.com"
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"trenduser_v2_{uuid.uuid4().hex[:8]}",
        "role": "operator",
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]
# =============================================================================
# TREND-1: PDF报告生成测试
# =============================================================================

def test_generate_trend_report_pdf(client):
    """🔴 测试 生成PDF报告"""
    token = get_auth_token(client)
    # 先创建报告
    response = client.post(
        "/trend-scout/reports",
        json={
            "query": "猫咪驱虫",
            "stage_filter": "AWARENESS",
            "audience_segment_ids": ["segment_1", "segment_2"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    report_id = response.json()["id"]
    
    # 生成PDF
    response = client.post(
        f"/trend-scout/reports/{report_id}/generate-pdf",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert "pdf_url" in data
    assert data["pdf_url"].endswith(".pdf")
    assert "report_html" in data  # 同时返回HTML预览


def test_trend_report_has_watermark(client):
    """🔴 测试 PDF报告含水印（下载人、时间）"""
    token = get_auth_token(client)
    response = client.post(
        "/trend-scout/reports",
        json={"query": "水印测试"},
        headers={"Authorization": f"Bearer {token}"},
    )
    report_id = response.json()["id"]
    
    response = client.post(
        f"/trend-scout/reports/{report_id}/generate-pdf",
        headers={"Authorization": f"Bearer {token}"},
    )
    data = response.json()
    # 验证水印信息
    assert data["watermark"]["downloader"].startswith("trenduser_v2")
    assert "download_time" in data["watermark"]
    assert data["watermark"]["disclaimer"] == "内部资料，禁止外传"


# =============================================================================
# TREND-2: 5A阶段匹配度计算测试
# =============================================================================

def test_trend_report_5a_stage_match(client):
    """🔴 测试 推荐选题清单含5A阶段匹配度"""
    token = get_auth_token(client)
    response = client.post(
        "/trend-scout/reports",
        json={
            "query": "驱虫攻略",
            "stage_filter": "AWARENESS",  # AIPL格式，应映射到5A
            "audience_segment_ids": ["new_cat_owner"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    
    # 验证返回5A相关信息
    assert "recommended_topics" in data
    assert len(data["recommended_topics"]) >= 1
    
    topic = data["recommended_topics"][0]
    assert "stage_match" in topic  # 5A阶段匹配
    assert topic["stage_match"] in ["AWARE", "APPEAL", "ASK", "ACT", "ADVOCATE"]
    assert "stage_match_score" in topic  # 匹配度分数
    assert 0 <= topic["stage_match_score"] <= 100


def test_trend_report_stage_filter_5a_mapping(client):
    """🔴 测试 stage_filter支持AIPL和5A双格式"""
    token = get_auth_token(client)
    
    # AIPL格式
    response = client.post(
        "/trend-scout/reports",
        json={"query": "AIPL测试", "stage_filter": "AWARENESS"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    
    # 5A格式
    response = client.post(
        "/trend-scout/reports",
        json={"query": "5A测试", "stage_filter": "APPEAL"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201


# =============================================================================
# TREND-3: 人群契合度评分测试
# =============================================================================

def test_trend_report_audience_fit_score(client):
    """🔴 测试 推荐选题含目标人群契合度评分"""
    token = get_auth_token(client)
    response = client.post(
        "/trend-scout/reports",
        json={
            "query": "新手养猫",
            "audience_segment_ids": ["new_cat_owner", "budget_conscious"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    
    assert "recommended_topics" in data
    for topic in data["recommended_topics"]:
        assert "audience_fit_score" in topic  # 人群契合度
        assert 0 <= topic["audience_fit_score"] <= 100


def test_trend_report_target_audience_info(client):
    """🔴 测试 报告含目标人群信息"""
    token = get_auth_token(client)
    response = client.post(
        "/trend-scout/reports",
        json={
            "query": "目标人群测试",
            "audience_segment_ids": ["segment_1"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    data = response.json()
    assert "target_audience" in data
    assert data["target_audience"]["segment_ids"] == ["segment_1"]


# =============================================================================
# TREND-4: 预估互动区间测试 (PoolPredictor先验)
# =============================================================================

def test_trend_report_engagement_interval(client):
    """🔴 测试 推荐选题含预估互动区间，标注为参考"""
    token = get_auth_token(client)
    response = client.post(
        "/trend-scout/reports",
        json={"query": "互动预测测试"},
        headers={"Authorization": f"Bearer {token}"},
    )
    data = response.json()
    
    assert "recommended_topics" in data
    topic = data["recommended_topics"][0]
    
    # 验证互动区间
    assert "engagement_interval" in topic
    interval = topic["engagement_interval"]
    assert "likes" in interval
    assert "comments" in interval
    assert "saves" in interval
    assert "lower" in interval["likes"]
    assert "median" in interval["likes"]
    assert "upper" in interval["likes"]
    
    # 关键: 必须标注为参考区间
    assert interval["disclaimer"] == "内部参考区间，非平台真实数据"


# =============================================================================
# TRENT-5: 批量报告生成测试
# =============================================================================

def test_batch_generate_trend_reports(client):
    """🔴 测试 为多账号批量生成选题报告"""
    token = get_auth_token(client)
    response = client.post(
        "/trend-scout/reports/batch",
        json={
            "query": "批量驱虫报告",
            "stage_filter": "AWARE",
            "account_ids": ["acc_1", "acc_2", "acc_3"],
            "audience_segment_ids": ["segment_1"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert "batch_id" in data
    assert data["total_accounts"] == 3
    assert "report_ids" in data
    assert len(data["report_ids"]) == 3


def test_batch_reports_individual_access(client):
    """🔴 测试 批量生成的报告可单独访问"""
    token = get_auth_token(client)
    
    # 批量创建
    batch_resp = client.post(
        "/trend-scout/reports/batch",
        json={
            "query": "批量访问测试",
            "account_ids": ["acc_a", "acc_b"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    report_ids = batch_resp.json()["report_ids"]
    
    # 单独访问每个报告
    for rid in report_ids:
        response = client.get(
            f"/trend-scout/reports/{rid}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["id"] == rid


# =============================================================================
# TREND-6: 在线预览报告测试
# =============================================================================

def test_preview_trend_report(client):
    """🔴 测试 在线预览报告HTML"""
    token = get_auth_token(client)
    
    # 创建报告
    create_resp = client.post(
        "/trend-scout/reports",
        json={"query": "预览测试"},
        headers={"Authorization": f"Bearer {token}"},
    )
    report_id = create_resp.json()["id"]
    
    # 预览
    response = client.get(
        f"/trend-scout/reports/{report_id}/preview",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "html_content" in data
    assert "瑞德医生" in data["html_content"]  # 品牌Logo注入


# =============================================================================
# TREND-7: 报告下载测试
# =============================================================================

def test_download_trend_report(client):
    """🔴 测试 下载报告PDF"""
    token = get_auth_token(client)
    
    create_resp = client.post(
        "/trend-scout/reports",
        json={"query": "下载测试"},
        headers={"Authorization": f"Bearer {token}"},
    )
    report_id = create_resp.json()["id"]
    
    # 先生成PDF
    client.post(
        f"/trend-scout/reports/{report_id}/generate-pdf",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    # 下载
    response = client.get(
        f"/trend-scout/reports/{report_id}/download",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    # API返回PDF信息而不是直接下载文件
    assert data["content_type"] == "application/pdf"
    assert "pdf_url" in data
    assert data["disclaimer"] == "内部资料，禁止外传"


# =============================================================================
# TREND-8: 报告详情增强测试
# =============================================================================

def test_trend_report_detail_v2_enhancements(client):
    """🔴 测试 报告详情包含V2.7.1增强字段"""
    token = get_auth_token(client)
    
    response = client.post(
        "/trend-scout/reports",
        json={
            "query": "详情测试",
            "stage_filter": "AWARE",
            "audience_segment_ids": ["seg_1"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    report_id = response.json()["id"]
    
    # 获取详情
    detail_resp = client.get(
        f"/trend-scout/reports/{report_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    data = detail_resp.json()
    
    # V2.7.1新增字段
    assert "report_html" in data
    assert "report_pdf_url" in data
    assert "recommended_topics" in data
    assert "target_audience" in data
    assert "brand_knowledge_refs" in data
