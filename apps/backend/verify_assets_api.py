#!/usr/bin/env python3
"""验证素材库 API 的完整流程: 列表 + 创建 + 列表."""
import requests
import uuid

BASE = "http://localhost:8000"

email = f"v_{uuid.uuid4().hex[:8]}@ecodream.com"
reg = requests.post(f"{BASE}/auth/register", json={
    "email": email, "password": "SecurePass123!", "username": f"v_{uuid.uuid4().hex[:8]}", "role": "operator"
})
token = reg.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("=" * 60)
print("素材库 API 验证")
print("=" * 60)

# 1. 列表
r = requests.get(f"{BASE}/assets", headers=headers)
data = r.json()
print(f"\n[1] 列表: 返回 {data.get('total')} 条")
for a in data.get("items", [])[:2]:
    print(f"    {a.get('filename')} | {a.get('file_url','')[:50]}...")

# 2. 创建
payload = {
    "filename": "测试素材-猫一只",
    "file_url": "https://qcloud.dpfile.com/pc/le8uKNDuy66RmWfP_yqFJrLFKqn_EvTDetdUfxFhhZpmEW2sFeaPPrN-mLIZjIucY0q73sB2DyQcgmKUxZFQtw.jpg",
    "source_type": "OPERATOR_UPLOAD",
    "license_type": "OWNED",
    "tags": ["猫", "测试"],
    "category": "image",
    "generate_thumbnail": False,
}
r = requests.post(f"{BASE}/assets/upload", json=payload, headers=headers)
print(f"\n[2] 创建: status={r.status_code}")
if r.status_code == 201:
    created = r.json()
    print(f"    新素材 ID: {created['id']}")

    # 3. 再次列表
    r2 = requests.get(f"{BASE}/assets", headers=headers)
    data2 = r2.json()
    print(f"\n[3] 再次列表: 返回 {data2.get('total')} 条")
    found = any(a.get('filename') == '测试素材-猫一只' for a in data2.get('items', []))
    print(f"    新素材是否出现: {'是' if found else '否'}")

print("\n" + "=" * 60)
