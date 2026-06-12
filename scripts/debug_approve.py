import requests
import json
import time
import sys

BASE = 'http://localhost:8000'

# Login
r = requests.post(f'{BASE}/auth/login', json={'email':'tester@ecodream.com','password':'test123456'})
if r.status_code != 200:
    print('Login failed:', r.status_code, r.text)
    sys.exit(1)
token = r.json()['access_token']
print('Token OK')

# Create task
r = requests.post(
    f'{BASE}/task-hub/tasks/with-workflow',
    headers={'Authorization': f'Bearer {token}'},
    json={
        'name': 'DEBUG_PUBLISH',
        'workflow_template_id': 'content_creation_note_image',
        'workflow_version': 1,
        'account_id': '2WjXFAYpQvgJfuvE4Ms0RA',
        'persona_id': 'p1',
        'platform': 'xhs',
        'content_format': 'note_image',
        'prompt_variables': {'topic': '猫咪健康'}
    }
)
print('Create status:', r.status_code)
if r.status_code != 201:
    print('Create response:', r.text)
    sys.exit(1)
task = r.json()
task_id = task['id']
print('Task ID:', task_id)
print('Initial status:', task['status'])

# Wait for human_wait
for i in range(30):
    time.sleep(1)
    r = requests.get(f'{BASE}/task-hub/tasks/{task_id}', headers={'Authorization': f'Bearer {token}'})
    t = r.json()
    if t['status'] == 'human_wait':
        print('Reached human_wait at node', t.get('current_node_index'))
        break
    st = t['status']
    ni = t.get('current_node_index')
    print(f'  wait... status={st} node={ni}')
else:
    print('Timeout waiting for human_wait')
    sys.exit(1)

# APPROVE
print('\n--- Sending APPROVE ---')
r = requests.post(
    f'{BASE}/task-hub/tasks/{task_id}/human-decision',
    headers={'Authorization': f'Bearer {token}'},
    json={'decision': 'APPROVE', 'feedback': '', 'operator': 'reality_tester'}
)
print('APPROVE status:', r.status_code)
if r.status_code != 200:
    print('Response body:', r.text)
else:
    result = r.json()
    try:
        print('Result:', json.dumps(result, indent=2, ensure_ascii=False))
    except UnicodeEncodeError:
        print('Result (ascii):', json.dumps(result, indent=2, ensure_ascii=True))
    
    # Check final status
    time.sleep(3)
    r = requests.get(f'{BASE}/task-hub/tasks/{task_id}', headers={'Authorization': f'Bearer {token}'})
    t = r.json()
    print('Final status:', t['status'])
    print('Final node_index:', t.get('current_node_index'))
    print('Review decision:', t.get('review_decision'))
