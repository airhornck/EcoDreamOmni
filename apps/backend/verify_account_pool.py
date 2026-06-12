#!/usr/bin/env python3
import requests

BASE = "http://localhost:8000"

# 使用上一步注册的凭据登录（或重新注册）
import uuid
email = f"v_{uuid.uuid4().hex[:8]}@ecodream.com"
reg = requests.post(f"{BASE}/auth/register", json={
    "email": email, "password": "SecurePass123!", "username": f"v_{uuid.uuid4().hex[:8]}", "role": "operator"
})
token = reg.json()["access_token"]

# 获取账号列表
res = requests.get(f"{BASE}/account-pool", headers={"Authorization": f"Bearer {token}"})
data = res.json()
print("Status:", res.status_code)
print("Total accounts:", data.get("total"))
print("Stats:", data.get("stats"))
for a in data.get("accounts", []):
    print(f"  - {a['account_id']} | {a['nickname']} | {a['platform']} | persona={a['persona']} | phase={a['lifecycle_phase']} | health={a['health_score']}")
