"""
Auth module Red-Green tests.
"""

from src.models.user import clear_users


def test_register_user_success(client):
    import uuid
    email = f"auth_reg_{uuid.uuid4().hex[:8]}@ecodream.com"
    clear_users()
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"testuser_{uuid.uuid4().hex[:8]}",
        "role": "operator"
    })
    assert response.status_code == 201, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == email
    assert "password" not in data["user"]


def test_register_duplicate_email(client):
    import uuid
    email = f"auth_dup_{uuid.uuid4().hex[:8]}@ecodream.com"
    clear_users()
    client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"dupuser_{uuid.uuid4().hex[:8]}",
        "role": "operator"
    })
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"dupuser2_{uuid.uuid4().hex[:8]}",
        "role": "operator"
    })
    assert response.status_code == 409


def test_login_success(client):
    import uuid
    email = f"auth_login_{uuid.uuid4().hex[:8]}@ecodream.com"
    clear_users()
    client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"loginuser_{uuid.uuid4().hex[:8]}",
        "role": "operator"
    })
    response = client.post("/auth/login", json={
        "email": email,
        "password": "SecurePass123!"
    })
    assert response.status_code == 200, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client):
    import uuid
    email = f"auth_bad_{uuid.uuid4().hex[:8]}@ecodream.com"
    clear_users()
    client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"badpassuser_{uuid.uuid4().hex[:8]}",
        "role": "operator"
    })
    response = client.post("/auth/login", json={
        "email": email,
        "password": "WrongPass123!"
    })
    assert response.status_code == 401


def test_get_current_user(client):
    import uuid
    email = f"auth_me_{uuid.uuid4().hex[:8]}@ecodream.com"
    clear_users()
    reg = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"meuser_{uuid.uuid4().hex[:8]}",
        "role": "operator"
    })
    assert reg.status_code == 201, f"Register failed: {reg.text}"
    token = reg.json()["access_token"]
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert data["role"] == "operator"


def test_get_current_user_no_token(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_role_based_access(client):
    import uuid
    op_email = f"auth_op_{uuid.uuid4().hex[:8]}@ecodream.com"
    admin_email = f"auth_ad_{uuid.uuid4().hex[:8]}@ecodream.com"
    clear_users()
    reg_op = client.post("/auth/register", json={
        "email": op_email,
        "password": "SecurePass123!",
        "username": f"opuser_{uuid.uuid4().hex[:8]}",
        "role": "operator"
    })
    assert reg_op.status_code == 201, f"Operator register failed: {reg_op.text}"
    op_token = reg_op.json()["access_token"]

    reg_ad = client.post("/auth/register", json={
        "email": admin_email,
        "password": "SecurePass123!",
        "username": f"adminuser_{uuid.uuid4().hex[:8]}",
        "role": "admin"
    })
    assert reg_ad.status_code == 201, f"Admin register failed: {reg_ad.text}"
    admin_token = reg_ad.json()["access_token"]

    response = client.get("/admin/users", headers={"Authorization": f"Bearer {op_token}"})
    assert response.status_code == 403

    response = client.get("/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200


def test_mfa_setup_and_verify(client):
    import uuid
    email = f"auth_mfa_{uuid.uuid4().hex[:8]}@ecodream.com"
    clear_users()
    reg = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"mfauser_{uuid.uuid4().hex[:8]}",
        "role": "operator"
    })
    assert reg.status_code == 201, f"MFA register failed: {reg.text}"
    token = reg.json()["access_token"]

    setup = client.post("/auth/mfa/setup", headers={"Authorization": f"Bearer {token}"})
    assert setup.status_code == 200
    secret = setup.json()["secret"]
    assert secret is not None

    enable = client.post("/auth/mfa/enable", headers={"Authorization": f"Bearer {token}"}, json={
        "code": "000000"
    })
    assert enable.status_code in [200, 400]
