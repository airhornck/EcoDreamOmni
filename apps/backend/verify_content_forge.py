#!/usr/bin/env python3
"""验证 Content Forge 各下拉框数据是否可正常获取."""
import requests
import uuid

BASE = "http://localhost:8000"

# 注册获取 token
email = f"v_{uuid.uuid4().hex[:8]}@ecodream.com"
reg = requests.post(f"{BASE}/auth/register", json={
    "email": email, "password": "SecurePass123!", "username": f"v_{uuid.uuid4().hex[:8]}", "role": "operator"
})
token = reg.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("=" * 60)
print("Content Forge 下拉框数据验证")
print("=" * 60)

# 1. Personas
r = requests.get(f"{BASE}/personas", headers=headers)
data = r.json()
personas = data.get("personas", [])
print(f"\n[1] Personas: 返回 {len(personas)} 条")
for p in personas[:3]:
    print(f"    id={p['id']}  nickname={p.get('nickname','N/A')}  pet_type={p.get('pet_type','N/A')}  name={p.get('name','N/A')}")

# 2. PersonaStories
r = requests.get(f"{BASE}/persona-stories?status=active", headers=headers)
data = r.json()
stories = data.get("items", [])
print(f"\n[2] PersonaStories: 返回 {len(stories)} 条")
for s in stories[:3]:
    print(f"    id={s['id']}  title={s.get('title','N/A')}  name={s.get('name','N/A')}  status={s['status']}")

# 3. StoryNodes (取第一个story)
if stories:
    story_id = stories[0]["id"]
    r = requests.get(f"{BASE}/persona-stories/{story_id}/nodes", headers=headers)
    nodes = r.json()
    print(f"\n[3] StoryNodes (story={story_id}): 返回 {len(nodes)} 条")
    for n in nodes[:3]:
        print(f"    id={n['id']}  title={n.get('title','N/A')}  mood={n.get('mood','N/A')}  theme={n.get('theme','N/A')}")

# 4. ContentSeries
r = requests.get(f"{BASE}/content-series", headers=headers)
data = r.json()
series = data.get("series", [])
print(f"\n[4] ContentSeries: 返回 {len(series)} 条")
for s in series[:3]:
    print(f"    id={s['id']}  name={s['name']}")

# 5. LLM Models
r = requests.get(f"{BASE}/llm-hub/models?status=active", headers=headers)
data = r.json()
models = data.get("items", [])
print(f"\n[5] LLM Models: 返回 {len(models)} 条")
for m in models[:4]:
    print(f"    id={m['id']}  name={m.get('name','N/A')}  provider={m['provider']}  model_name={m.get('model_name','N/A')}")

print("\n" + "=" * 60)
