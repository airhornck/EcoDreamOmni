#!/usr/bin/env python3
"""通过 API 为 Content Forge 补充 PersonaStory 默认数据."""
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

print("[OK] 注册成功，开始 seed PersonaStories...")

# 创建 Story 1
s1 = requests.post(f"{BASE}/persona-stories", json={
    "persona_id": "p1",
    "name": "毛孩子的第一次体检",
    "description": "记录带宠物第一次去医院体检的完整心路历程",
    "emotion_curve_template": "gradual_growth"
}, headers=headers).json()
print(f"[OK] Story 1: {s1['id']} - {s1['name']}")

# 为 Story 1 创建 nodes
for i, n in enumerate([
    {"sequence_index": 0, "theme": "出发前的紧张", "emotion_tone": "low", "key_event": "收拾宠物包，毛孩子似乎察觉到异样"},
    {"sequence_index": 1, "theme": "医院里的好奇", "emotion_tone": "medium", "key_event": "宠物对医院环境感到好奇，四处张望"},
    {"sequence_index": 2, "theme": "检查时的乖巧", "emotion_tone": "high", "key_event": "医生检查时宠物异常配合，获得表扬"},
    {"sequence_index": 3, "theme": "拿到健康报告", "emotion_tone": "burst", "key_event": "报告显示一切正常，心中的石头落地"},
]):
    requests.post(f"{BASE}/persona-stories/{s1['id']}/nodes", json=n, headers=headers)

# 创建 Story 2
s2 = requests.post(f"{BASE}/persona-stories", json={
    "persona_id": "p3",
    "name": "换粮大作战",
    "description": "从平价粮换到高端粮的七天过渡记录",
    "emotion_curve_template": "gradual_growth"
}, headers=headers).json()
print(f"[OK] Story 2: {s2['id']} - {s2['name']}")

for i, n in enumerate([
    {"sequence_index": 0, "theme": "第一天混粮", "emotion_tone": "low", "key_event": "新旧粮比例 3:7，宠物有点挑食"},
    {"sequence_index": 1, "theme": "第三天适应", "emotion_tone": "medium", "key_event": "比例调到 1:1，开始接受新粮"},
    {"sequence_index": 2, "theme": "第七天成功", "emotion_tone": "burst", "key_event": "完全换成新粮，毛发明显变亮"},
]):
    requests.post(f"{BASE}/persona-stories/{s2['id']}/nodes", json=n, headers=headers)

# 激活 stories
requests.patch(f"{BASE}/persona-stories/{s1['id']}/status", json={"status": "active"}, headers=headers)
requests.patch(f"{BASE}/persona-stories/{s2['id']}/status", json={"status": "active"}, headers=headers)

print("\n[完成] PersonaStory seed 完成，刷新页面即可看到")
