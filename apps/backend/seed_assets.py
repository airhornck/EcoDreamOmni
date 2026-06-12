#!/usr/bin/env python3
"""为素材库添加默认图片素材."""
import requests
import uuid

BASE = "http://localhost:8000"

# 注册获取 token
email = f"seed_{uuid.uuid4().hex[:8]}@ecodream.com"
reg = requests.post(f"{BASE}/auth/register", json={
    "email": email, "password": "SecurePass123!", "username": f"seed_{uuid.uuid4().hex[:8]}", "role": "operator"
})
token = reg.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("[OK] 注册成功，开始 seed 素材库...")

assets = [
    {
        "filename": "猫一只",
        "file_url": "https://qcloud.dpfile.com/pc/le8uKNDuy66RmWfP_yqFJrLFKqn_EvTDetdUfxFhhZpmEW2sFeaPPrN-mLIZjIucY0q73sB2DyQcgmKUxZFQtw.jpg",
        "source_type": "OPERATOR_UPLOAD",
        "license_type": "OWNED",
        "tags": ["猫", "宠物", "封面"],
        "category": "image",
    },
    {
        "filename": "可爱狗狗",
        "file_url": "https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?w=800&auto=format&fit=crop",
        "source_type": "OPERATOR_UPLOAD",
        "license_type": "OWNED",
        "tags": ["狗", "宠物", "封面"],
        "category": "image",
    },
    {
        "filename": "宠物医院",
        "file_url": "https://images.unsplash.com/photo-1628009368231-7bb7cfcb0def?w=800&auto=format&fit=crop",
        "source_type": "OPERATOR_UPLOAD",
        "license_type": "OWNED",
        "tags": ["医院", "宠物健康", "场景"],
        "category": "image",
    },
    {
        "filename": "猫粮对比",
        "file_url": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=800&auto=format&fit=crop",
        "source_type": "OPERATOR_UPLOAD",
        "license_type": "OWNED",
        "tags": ["猫粮", "对比", "测评"],
        "category": "image",
    },
]

for a in assets:
    r = requests.post(f"{BASE}/assets/upload", json=a, headers=headers)
    if r.status_code == 201:
        print(f"[OK] 添加素材: {a['filename']}")
    else:
        print(f"[FAIL] {a['filename']}: {r.status_code} {r.text[:100]}")

print("\n[完成] 素材库 seed 完成")
