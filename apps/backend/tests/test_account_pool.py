"""
W4 AccountPool Red-Green tests.
Tests for account pool CRUD, fingerprint engine, and Playwright context isolation.
"""

from src.models.user import clear_users
from src.services.auth_service import register_user



def get_auth_token(client, role: str = "operator"):
    import uuid
    clear_users()
    email = f"ap_{uuid.uuid4().hex[:8]}@ecodream.com"
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"apuser_{uuid.uuid4().hex[:8]}",
        "role": "operator",
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]
# ───────────────────────────────────────────────
# Account Pool CRUD
# ───────────────────────────────────────────────


def test_create_pool_account(client):
    """Red: Should create an account pool entry with fingerprint and lifecycle."""
    token = get_auth_token(client)
    payload = {
        "platform": "xhs",
        "account_id": "pool_xhs_001",
        "nickname": "素人号001",
        "cookie": "a1=xxx; webId=yyy",
        "persona": "宠物达人",
        "content_vertical": "宠物健康",
        "lifecycle_phase": "cold_start",
        "fingerprint_profile": {
            "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
            "viewport": {"width": 390, "height": 844},
            "locale": "zh-CN",
            "timezone": "Asia/Shanghai",
            "canvas_noise": True,
            "webgl_noise": True,
        },
        "proxy_config": {"type": "residential", "region": "上海"},
    }
    response = client.post(
        "/account-pool",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert data["platform"] == "xhs"
    assert data["account_id"] == "pool_xhs_001"
    assert data["persona"] == "宠物达人"
    assert data["lifecycle_phase"] == "cold_start"
    assert data["health_score"] == 100.0
    assert "id" in data
    assert "fingerprint_profile" in data
    assert data["fingerprint_profile"]["canvas_noise"] is True


def test_create_pool_account_requires_auth(client):
    """Red: Creating pool account should require authentication."""
    response = client.post("/account-pool", json={"platform": "xhs", "account_id": "x"})
    assert response.status_code == 401


def test_list_pool_accounts(client):
    """Red: Should list account pool with filtering by lifecycle_phase."""
    from src.models.account_pool import clear_pool_entries
    clear_pool_entries()
    token = get_auth_token(client)
    client.post(
        "/account-pool",
        json={
            "platform": "xhs",
            "account_id": "pool_xhs_001",
            "nickname": "素人号001",
            "cookie": "a1=xxx",
            "persona": "宠物达人",
            "content_vertical": "宠物健康",
            "lifecycle_phase": "cold_start",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    client.post(
        "/account-pool",
        json={
            "platform": "douyin",
            "account_id": "pool_dy_001",
            "nickname": "抖音素人001",
            "cookie": "sessionid=yyy",
            "persona": "生活博主",
            "content_vertical": "宠物日常",
            "lifecycle_phase": "growth",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    # List all
    response = client.get("/account-pool", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["accounts"]) == 2

    # Filter by lifecycle_phase
    response = client.get(
        "/account-pool?lifecycle_phase=cold_start",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["accounts"]) == 1
    assert data["accounts"][0]["lifecycle_phase"] == "cold_start"


def test_get_pool_account_detail(client):
    """Red: Should get pool account detail with full fingerprint."""
    token = get_auth_token(client)
    create_resp = client.post(
        "/account-pool",
        json={
            "platform": "xhs",
            "account_id": "pool_xhs_002",
            "nickname": "素人号002",
            "cookie": "a1=aaa",
            "persona": "科普达人",
            "content_vertical": "宠物医疗",
            "lifecycle_phase": "mature",
            "fingerprint_profile": {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "viewport": {"width": 1920, "height": 1080},
                "locale": "zh-CN",
                "timezone": "Asia/Shanghai",
                "canvas_noise": False,
                "webgl_noise": False,
            },
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    account_id = create_resp.json()["id"]

    response = client.get(f"/account-pool/{account_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["account_id"] == "pool_xhs_002"
    assert data["persona"] == "科普达人"
    assert data["fingerprint_profile"]["viewport"]["width"] == 1920


def test_update_pool_account_status(client):
    """Red: Should update pool account status and lifecycle."""
    token = get_auth_token(client)
    create_resp = client.post(
        "/account-pool",
        json={
            "platform": "xhs",
            "account_id": "pool_xhs_003",
            "nickname": "素人号003",
            "cookie": "a1=old",
            "persona": "新手",
            "content_vertical": "宠物健康",
            "lifecycle_phase": "cold_start",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    account_id = create_resp.json()["id"]

    response = client.patch(
        f"/account-pool/{account_id}",
        json={"lifecycle_phase": "growth", "health_score": 85.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["lifecycle_phase"] == "growth"
    assert data["health_score"] == 85.0


def test_delete_pool_account(client):
    """Red: Should delete a pool account."""
    token = get_auth_token(client)
    create_resp = client.post(
        "/account-pool",
        json={
            "platform": "xhs",
            "account_id": "pool_xhs_004",
            "nickname": "素人号004",
            "cookie": "a1=zzz",
            "persona": "测试",
            "content_vertical": "宠物",
            "lifecycle_phase": "cold_start",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    account_id = create_resp.json()["id"]

    response = client.delete(f"/account-pool/{account_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204

    get_resp = client.get(f"/account-pool/{account_id}", headers={"Authorization": f"Bearer {token}"})
    assert get_resp.status_code == 404


# ───────────────────────────────────────────────
# Fingerprint Engine
# ───────────────────────────────────────────────


def test_fingerprint_profile_generation():
    """Red: Should generate a random fingerprint profile for a new account."""
    from src.services.fingerprint_engine import generate_fingerprint

    fp1 = generate_fingerprint()
    fp2 = generate_fingerprint()

    assert "user_agent" in fp1
    assert "viewport" in fp1
    assert "locale" in fp1
    assert "timezone" in fp1
    assert "canvas_noise" in fp1
    assert "webgl_noise" in fp1
    # Two generated fingerprints should differ
    assert fp1["user_agent"] != fp2["user_agent"] or fp1["viewport"] != fp2["viewport"]


def test_fingerprint_viewport_from_pool():
    """Red: Fingerprint viewport should be one of predefined realistic sizes."""
    from src.services.fingerprint_engine import generate_fingerprint

    fp = generate_fingerprint()
    width = fp["viewport"]["width"]
    height = fp["viewport"]["height"]
    valid_sizes = [
        (390, 844), (393, 852), (360, 780), (414, 896),  # Mobile
        (1920, 1080), (2560, 1440), (1366, 768), (1440, 900), (1536, 864), (1280, 800),  # Desktop
        (820, 1180), (768, 1024), (834, 1194),  # Tablet
    ]
    assert (width, height) in valid_sizes


# ───────────────────────────────────────────────
# Health Score
# ───────────────────────────────────────────────


def test_health_score_calculation():
    """Red: Should calculate health score based on account metrics."""
    from src.services.account_health import calculate_health_score

    score = calculate_health_score(
        posts_today=3,
        posts_week=15,
        engagement_rate=0.05,
        violation_count=0,
        last_login_days=1,
    )
    assert 0 <= score <= 100
    assert isinstance(score, float)

    # More violations = lower score
    score_with_violations = calculate_health_score(
        posts_today=3,
        posts_week=15,
        engagement_rate=0.05,
        violation_count=2,
        last_login_days=1,
    )
    assert score_with_violations < score


# ───────────────────────────────────────────────
# Browser Context Isolation
# ───────────────────────────────────────────────


def test_browser_context_isolation_config():
    """Red: Should generate Playwright context config with fingerprint isolation."""
    from src.services.browser_pool import build_context_config

    fingerprint = {
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
        "viewport": {"width": 390, "height": 844},
        "locale": "zh-CN",
        "timezone": "Asia/Shanghai",
        "canvas_noise": True,
        "webgl_noise": True,
    }
    proxy = {"type": "residential", "region": "上海"}

    config = build_context_config(fingerprint, proxy)
    assert config["user_agent"] == fingerprint["user_agent"]
    assert config["viewport"] == fingerprint["viewport"]
    assert config["locale"] == fingerprint["locale"]
    assert config["timezone_id"] == fingerprint["timezone"]
    assert config["bypass_csp"] is True


def test_browser_pool_lifecycle():
    """Red: BrowserPool should track launched contexts and close cleanly."""
    from src.services.browser_pool import BrowserPool

    pool = BrowserPool()
    assert pool.launched_count == 0

    # Simulate launching a context (MVP: just track state)
    pool.mark_launched("ctx_001")
    assert pool.launched_count == 1
    assert "ctx_001" in pool.active_contexts

    pool.mark_closed("ctx_001")
    assert pool.launched_count == 1  # total launched doesn't decrease
    assert "ctx_001" not in pool.active_contexts
