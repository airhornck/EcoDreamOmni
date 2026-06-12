import requests, json, time, sys

BASE = 'http://localhost:8000'

# Login
r = requests.post(f'{BASE}/auth/login', json={'email':'tester@ecodream.com','password':'test123456'})
token = r.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Get first xhs account
r = requests.get(f'{BASE}/account-pool', headers=headers)
data = r.json()
accounts = data.get('accounts', []) if isinstance(data, dict) else data
xhs_accounts = [a for a in accounts if a.get('platform') in ('xiaohongshu', 'xhs')]
if not xhs_accounts:
    print('No XHS account found')
    sys.exit(1)
acc_id = xhs_accounts[0]['id']
print(f'Using account: {acc_id}')

# Create a task with a unique topic to ensure fresh LLM generation
unique_topic = f"LLM_VERIFY_{int(time.time())}"
print(f"Creating task with topic: {unique_topic}")

r = requests.post(
    f'{BASE}/task-hub/tasks/with-workflow',
    headers=headers,
    json={
        'name': unique_topic,
        'workflow_template_id': 'content_creation_note_image',
        'workflow_version': 1,
        'account_id': acc_id,
        'persona_id': 'p1',
        'platform': 'xhs',
        'content_format': 'note_image',
        'prompt_variables': {'topic': unique_topic}
    }
)
task = r.json()
task_id = task['id']
print(f'Task ID: {task_id}')

# Wait for human_wait
for i in range(30):
    time.sleep(1)
    r = requests.get(f'{BASE}/task-hub/tasks/{task_id}', headers=headers)
    t = r.json()
    if t['status'] == 'human_wait':
        print('Reached human_wait')
        break
else:
    print('Timeout')
    sys.exit(1)

# APPROVE
r = requests.post(
    f'{BASE}/task-hub/tasks/{task_id}/human-decision',
    headers=headers,
    json={'decision': 'APPROVE', 'feedback': '', 'operator': 'reality_tester'}
)
if r.status_code != 200:
    print(f'APPROVE failed: {r.status_code} {r.text}')
    sys.exit(1)

# Wait for completion
for i in range(30):
    time.sleep(1)
    r = requests.get(f'{BASE}/task-hub/tasks/{task_id}', headers=headers)
    t = r.json()
    if t['status'] in ('completed', 'failed'):
        print(f'Final status: {t["status"]}')
        break
else:
    print('Timeout waiting for completion')
    sys.exit(1)

# Extract and verify generated content
pv = t.get('prompt_variables', {})
gc = pv.get('generated_content', {})

# Save full result to file for inspection
with open('D:/project/EcoDreamOmni/scripts/llm_verify_result.json', 'w', encoding='utf-8') as f:
    json.dump({'task_id': task_id, 'status': t['status'], 'generated_content': gc}, f, ensure_ascii=False, indent=2)
print('Saved result to llm_verify_result.json')

body = gc.get('body', '')
title = gc.get('title', '')

checks = {
    'body_not_empty': len(body) > 100,
    'title_not_empty': len(title) > 5,
    'has_emoji': any(ord(c) > 0x1F300 for c in body + title),
    'has_markdown_headers': '##' in body,
    'has_persona_voice': '铲' in body or '喵' in body or '主子' in body,
    'has_platform_style': len([c for c in body if ord(c) > 0x1F300]) > 5,
    'no_llm_error': '_llm_error' not in str(pv),
}

print("\n=== LLM Call Verification ===")
all_pass = True
for name, result in checks.items():
    status = "PASS" if result else "FAIL"
    if not result:
        all_pass = False
    print(f"  {name}: {status}")

print(f"\nBody length: {len(body)} chars")
try:
    print(f"Title preview: {title[:60]}...")
except UnicodeEncodeError:
    print(f"Title preview: {title[:60].encode('ascii', 'replace').decode()}...")

if all_pass:
    print("\nLLM real call verification PASSED")
else:
    print("\nLLM real call verification FAILED")
    sys.exit(1)
