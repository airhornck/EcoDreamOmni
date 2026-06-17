"""
W3.5 PlatformAccountManager Red-Green tests.
Tests for platform account login, cookie vault, and session management.
"""

from src.models.user import clear_users



def get_auth_token(client, role: str = "operator"):
    import uuid
    clear_users()
    email = f"pa_{uuid.uuid4().hex[:8]}@ecodream.com"
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"pauser_{uuid.uuid4().hex[:8]}",
        "role": "operator",
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]
# ───────────────────────────────────────────────
# Platform Account CRUD
# ───────────────────────────────────────────────


def test_create_platform_account(client):
    """Red Should create a platform account with cookie."""
    token = get_auth_token(client)
    payload = {
        "platform": "xhs",
        "account_id": "acc_xhs_001",
        "nickname": "小红薯001",
        "cookie": "a1=xxx; webId=yyy; web_session=zzz",
        "status": "active",
    }
    response = client.post(
        "/platform-accounts",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert data["platform"] == "xhs"
    assert data["account_id"] == "acc_xhs_001"
    assert data["nickname"] == "小红薯001"
    assert "id" in data
    assert data["status"] == "active"


def test_create_platform_account_requires_auth(client):
    """Red Creating account should require authentication."""
    response = client.post("/platform-accounts", json={"platform": "xhs", "account_id": "x"})
    assert response.status_code == 401


def test_list_platform_accounts(client):
    """Red Should list all platform accounts."""
    from src.models.platform_account import clear_platform_accounts
    clear_platform_accounts()
    token = get_auth_token(client)
    # Create two accounts
    client.post(
        "/platform-accounts",
        json={
            "platform": "xhs",
            "account_id": "acc_xhs_001",
            "nickname": "小红薯001",
            "cookie": "a1=xxx",
            "status": "active",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    client.post(
        "/platform-accounts",
        json={
            "platform": "douyin",
            "account_id": "acc_dy_001",
            "nickname": "抖音001",
            "cookie": "sessionid=yyy",
            "status": "active",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.get("/platform-accounts", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "accounts" in data
    assert len(data["accounts"]) == 2
    platforms = {a["platform"] for a in data["accounts"]}
    assert platforms == {"xhs", "douyin"}


def test_get_platform_account_detail(client):
    """Red Should get a single platform account detail."""
    token = get_auth_token(client)
    create_resp = client.post(
        "/platform-accounts",
        json={
            "platform": "xhs",
            "account_id": "acc_xhs_002",
            "nickname": "小红薯002",
            "cookie": "a1=aaa",
            "status": "active",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    account_id = create_resp.json()["id"]

    response = client.get(f"/platform-accounts/{account_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["account_id"] == "acc_xhs_002"
    assert data["nickname"] == "小红薯002"


def test_update_platform_account_cookie(client):
    """Red Should update account cookie."""
    token = get_auth_token(client)
    create_resp = client.post(
        "/platform-accounts",
        json={
            "platform": "xhs",
            "account_id": "acc_xhs_003",
            "nickname": "小红薯003",
            "cookie": "a1=old",
            "status": "active",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    account_id = create_resp.json()["id"]

    response = client.patch(
        f"/platform-accounts/{account_id}",
        json={"cookie": "a1=new; webId=new"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    # Verify cookie updated
    detail = client.get(f"/platform-accounts/{account_id}", headers={"Authorization": f"Bearer {token}"})
    # Cookie should be decrypted and returned (or at least not equal to raw encrypted)
    assert detail.status_code == 200


def test_delete_platform_account(client):
    """Red Should delete a platform account."""
    token = get_auth_token(client)
    create_resp = client.post(
        "/platform-accounts",
        json={
            "platform": "xhs",
            "account_id": "acc_xhs_004",
            "nickname": "小红薯004",
            "cookie": "a1=zzz",
            "status": "active",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    account_id = create_resp.json()["id"]

    response = client.delete(f"/platform-accounts/{account_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204

    # Verify deletion
    get_resp = client.get(f"/platform-accounts/{account_id}", headers={"Authorization": f"Bearer {token}"})
    assert get_resp.status_code == 404


# ───────────────────────────────────────────────
# Cookie Vault (Encryption)
# ───────────────────────────────────────────────


def test_cookie_is_encrypted_in_storage():
    """Red: Cookie should be encrypted when stored and decrypted when read."""
    from src.models.platform_account import create_platform_account, get_platform_account, _platform_account_db

    _platform_account_db.clear()
    account = create_platform_account(
        platform="xhs",
        account_id="enc_test_001",
        nickname="加密测试",
        cookie="a1=secret_value; webId=secret_id",
        status="active",
    )
    # Raw storage should contain encrypted data, not plaintext
    raw = _platform_account_db[account.id]
    assert "secret_value" not in raw.cookie_encrypted
    assert "secret_id" not in raw.cookie_encrypted

    # Decrypted retrieval should contain plaintext
    retrieved = get_platform_account(account.id)
    assert retrieved is not None
    assert retrieved.cookie == "a1=secret_value; webId=secret_id"


# ───────────────────────────────────────────────
# Session Status Check
# ───────────────────────────────────────────────


def test_session_status_check(client):
    """Red Should check if a platform account session is valid."""
    token = get_auth_token(client)
    create_resp = client.post(
        "/platform-accounts",
        json={
            "platform": "xhs",
            "account_id": "acc_xhs_005",
            "nickname": "小红薯005",
            "cookie": "a1=test",
            "status": "active",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    account_id = create_resp.json()["id"]

    response = client.get(
        f"/platform-accounts/{account_id}/session-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "status" in data  # valid, expired, unknown
    assert data["status"] in ("valid", "expired", "unknown")


# ───────────────────────────────────────────────
# QR Code Login Flow
# ───────────────────────────────────────────────


def test_qr_login_start(client):
    """Red Should initiate QR code login for a platform."""
    token = get_auth_token(client)
    response = client.post(
        "/platform-accounts/qr-login/start",
        json={"platform": "xhs"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "qr_id" in data
    assert "qr_url" in data
    assert data["platform"] == "xhs"


def test_qr_login_poll(client):
    """Red Should poll QR login status."""
    token = get_auth_token(client)
    start_resp = client.post(
        "/platform-accounts/qr-login/start",
        json={"platform": "xhs"},
        headers={"Authorization": f"Bearer {token}"},
    )
    qr_id = start_resp.json()["qr_id"]

    response = client.get(
        "/platform-accounts/qr-login/poll",
        params={"qr_id": qr_id, "platform": "xhs"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "status" in data  # pending, scanned, confirmed, expired
    assert data["status"] in ("pending", "scanned", "confirmed", "expired")
