import requests, json, sys

BASE = 'http://localhost:8000'

# Login
r = requests.post(f'{BASE}/auth/login', json={'email':'tester@ecodream.com','password':'test123456'})
token = r.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

print("=== 1. 账号池检查 ===")
r = requests.get(f'{BASE}/account-pool', headers=headers)
data = r.json()
accounts = data.get('accounts', []) if isinstance(data, dict) else data

for acc in accounts:
    print(f"\n账号: {acc.get('nickname')} ({acc.get('id')})")
    print(f"  platform: {acc.get('platform')}")
    print(f"  lifecycle: {acc.get('lifecycle_phase')}")
    print(f"  posts_today: {acc.get('posts_today')}")
    print(f"  daily_quota: {acc.get('daily_quota')}")
    print(f"  quota_exceeded: {acc.get('quota_exceeded')}")
    fp = acc.get('fingerprint_profile', {})
    print(f"  fingerprint_profile:")
    print(f"    user_agent: {fp.get('user_agent', 'N/A')[:80]}...")
    print(f"    viewport: {fp.get('viewport', 'N/A')}")
    print(f"    locale: {fp.get('locale', 'N/A')}")
    print(f"    timezone: {fp.get('timezone', 'N/A')}")
    print(f"    canvas_noise: {fp.get('canvas_noise', 'N/A')}")
    print(f"    webgl_noise: {fp.get('webgl_noise', 'N/A')}")
    pc = acc.get('proxy_config')
    if pc:
        print(f"  proxy_config: {pc}")
    else:
        print(f"  proxy_config: None (未配置代理)")

print("\n=== 2. 已发布任务检查 ===")
r = requests.get(f'{BASE}/task-hub/tasks', headers=headers)
tasks = r.json()

published_tasks = [t for t in tasks if t.get('status') == 'completed' and t.get('review_decision') == 'APPROVE']
print(f"找到 {len(published_tasks)} 个 completed + APPROVE 任务")

for t in published_tasks[:5]:
    pv = t.get('prompt_variables', {})
    gc = pv.get('generated_content', {})
    print(f"\n  Task: {t.get('name')[:40]}")
    print(f"    ID: {t.get('id')}")
    print(f"    Account: {t.get('account_id')}")
    print(f"    Status: {t.get('status')}")
    print(f"    Current node: {t.get('current_node_index')}")
    print(f"    Generated title: {gc.get('title', 'N/A')[:60]}...")
    # Check if publish_result is in prompt_variables
    if 'publish_result' in pv:
        print(f"    Publish result: {pv['publish_result']}")
    else:
        print(f"    Publish result: NOT in prompt_variables (执行上下文仅存内存)")

print("\n=== 3. 直接检查后端内存状态 ===")
# We can't easily access in-memory state from outside, but we can check proxy configs
r = requests.get(f'{BASE}/proxies', headers=headers)
if r.status_code == 200:
    proxies = r.json()
    print(f"代理配置数量: {len(proxies)}")
    for p in proxies:
        print(f"  {p.get('name', 'N/A')} - {p.get('protocol', 'N/A')}://{p.get('host', 'N/A')}:{p.get('port', 'N/A')} (active={p.get('is_active', False)})")
else:
    print(f"无法获取代理配置: {r.status_code} {r.text[:100]}")
