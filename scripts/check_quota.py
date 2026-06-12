import requests, json

BASE = 'http://localhost:8000'
r = requests.post(f'{BASE}/auth/login', json={'email':'tester@ecodream.com','password':'test123456'})
token = r.json()['access_token']

r = requests.get(f'{BASE}/account-pool', headers={'Authorization':f'Bearer {token}'})
print('Status:', r.status_code)
print('Type:', type(r.json()))
print('Body:', json.dumps(r.json(), indent=2, ensure_ascii=False)[:500])
