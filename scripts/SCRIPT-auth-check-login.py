import requests, json

BASE = 'http://localhost:8000'

def try_login(email, password):
    r = requests.post(f'{BASE}/auth/login', json={'email': email, 'password': password})
    print(f"Login: {email} / {password}")
    print(f"  Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"  Full response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return True
    else:
        print(f"  Error: {r.text[:300]}")
        return False

print("=== Testing available credentials ===\n")

print("[1] User-provided admin credentials:")
try_login('admin@ecodream.com', 'admin123')
print()

print("[2] E2E test credentials:")
try_login('tester@ecodream.com', 'test123456')
