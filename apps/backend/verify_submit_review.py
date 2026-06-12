#!/usr/bin/env python3
"""验证内容锻造提交审核完整流程."""
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
print("提交审核流程验证")
print("=" * 60)

# 1. 创建草稿（模拟前端提交的数据）
payload = {
    "title": "测试文章标题",
    "body": "这是测试文章正文内容...",
    "platform": "xhs",
    "tags": ["猫", "宠物健康"],
    "cover_image_url": "https://qcloud.dpfile.com/pc/le8uKNDuy66RmWfP_yqFJrLFKqn_EvTDetdUfxFhhZpmEW2sFeaPPrN-mLIZjIucY0q73sB2DyQcgmKUxZFQtw.jpg",
    "status": "draft",
}

r = requests.post(f"{BASE}/content-drafts", json=payload, headers=headers)
print(f"\n[1] 创建草稿: status={r.status_code}")
if r.status_code == 201:
    draft = r.json()
    print(f"    draft_id={draft['id']}")
    print(f"    title={draft['title']}")
    print(f"    cover_image_url={draft.get('cover_image_url', 'N/A')}")

    # 2. 提交审核
    r2 = requests.patch(f"{BASE}/content-drafts/{draft['id']}", json={"status": "reviewing"}, headers=headers)
    print(f"\n[2] 提交审核: status={r2.status_code}")
    if r2.status_code == 200:
        updated = r2.json()
        print(f"    status={updated['status']}")
        print(f"    cover_image_url={updated.get('cover_image_url', 'N/A')}")

    # 3. 列表确认
    r3 = requests.get(f"{BASE}/content-drafts", headers=headers)
    data = r3.json()
    print(f"\n[3] 草稿列表: total={data.get('total')}")
    for d in data.get("drafts", [])[:2]:
        print(f"    {d['id'][:20]}... | {d['title']} | status={d['status']} | cover={d.get('cover_image_url','N/A')[:40]}...")
else:
    print(f"    ERROR: {r.text}")

print("\n" + "=" * 60)
