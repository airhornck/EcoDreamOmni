import requests
import time

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
    exit(1)
acc_id = xhs_accounts[0]['id']
print(f'Using account: {acc_id}')

# Create task with a real Unsplash cover image topic
r = requests.post(
    f'{BASE}/task-hub/tasks/with-workflow',
    headers=headers,
    json={
        'name': '图片修复验证测试',
        'workflow_template_id': 'content_creation_note_image',
        'workflow_version': 1,
        'account_id': acc_id,
        'persona_id': 'p1',
        'platform': 'xhs',
        'content_format': 'note_image',
        'prompt_variables': {'topic': '猫咪夏季防暑'}
    }
)
task = r.json()
task_id = task['id']
print(f'Task ID: {task_id}')
print(f'Initial status: {task["status"]}')

# Wait for human_wait
for i in range(30):
    time.sleep(1)
    r = requests.get(f'{BASE}/task-hub/tasks/{task_id}', headers=headers)
    t = r.json()
    if t['status'] == 'human_wait':
        print('Reached human_wait')
        # Check the generated_content cover_image_url
        gc = t.get('prompt_variables', {}).get('generated_content', {})
        print(f'Cover image URL: {gc.get("cover_image_url", "N/A")}')
        break
    print(f'  wait... status={t["status"]}')
else:
    print('Timeout waiting for human_wait')
    exit(1)

# APPROVE
print('\nSending APPROVE...')
r = requests.post(
    f'{BASE}/task-hub/tasks/{task_id}/human-decision',
    headers=headers,
    json={'decision': 'APPROVE', 'feedback': '', 'operator': 'reality_tester'}
)
print(f'APPROVE status: {r.status_code}')
if r.status_code == 200:
    print('APPROVE succeeded')
else:
    print(f'APPROVE failed: {r.text[:300]}')

# Check final status
for i in range(10):
    time.sleep(1)
    r = requests.get(f'{BASE}/task-hub/tasks/{task_id}', headers=headers)
    t = r.json()
    if t['status'] in ('completed', 'failed'):
        print(f'Final status: {t["status"]}')
        break
    print(f'  wait... status={t["status"]}')

print('\nNow checking backend logs for "Downloaded cover image"...')
