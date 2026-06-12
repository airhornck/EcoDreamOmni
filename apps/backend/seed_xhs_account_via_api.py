#!/usr/bin/env python3
"""通过后端 API 将 XHS Cookie 写入账号池（自动注册获取 Token）."""

import json
import uuid

import requests

BASE_URL = "http://localhost:8000"

XHS_COOKIE = (
    "a1=19cdbf89844wtn4sjagtymcuh85j5qmuyqvhxhuta50000139209; "
    "webId=c627f37c5ca63300818755771909cc87; "
    "gid=yjSfDiY0W2vWyjSfDiYjYAx744E9I4MV0k9vh906S7xY2x28V2A67C888yqjJ8j88Yd2djKY; "
    "x-user-id-creator.xiaohongshu.com=66c1e7e8000000001d032e3d; "
    "customerClientId=529591855589904; "
    "abRequestId=c627f37c5ca63300818755771909cc87; "
    "ets=1779466635088; "
    "webBuild=6.12.1; "
    "websectiga=634d3ad75ffb42a2ade2c5e1705a73c845837578aeb31ba0e442d75c648da36a; "
    "sec_poison_id=14479410-ff3c-49af-94bd-d3b9a440ca74; "
    "web_session=040069b6405c5872c1b0702b27384bf5f770eb; "
    "id_token=VjEAALKw607dlBqNHEBlymQehILpsUyFYvIbavHV8d79Ff2UCDkB+/6snCdDFlwzTMMXc7qYtyShIac7THCJHOqAJAzcwvuSqj3qJSNoz/ToaAqsrkQYUQwY5QwXwxqLsjX5E8Kl; "
    "x-rednote-datactry=CN; "
    "x-rednote-holderctry=CN; "
    "unread=%7B%22ub%22%3A%226a087c0900000000360189ca%22%2C%22ue%22%3A%226a06aa07000000003501f817%22%2C%22uc%22%3A29%7D; "
    "xsecappid=ranchi; "
    "loadts=1779589970003"
)


def main():
    # 1. 注册获取 token
    email = f"seed_{uuid.uuid4().hex[:8]}@ecodream.com"
    password = "SecurePass123!"
    username = f"seed_{uuid.uuid4().hex[:8]}"

    reg_resp = requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": email, "password": password, "username": username, "role": "operator"},
    )
    if reg_resp.status_code != 201:
        print(f"注册失败: {reg_resp.status_code} {reg_resp.text}")
        return

    token = reg_resp.json()["access_token"]
    print(f"[OK] 注册成功，获取 token")

    # 2. 获取可用 personas
    personas_resp = requests.get(
        f"{BASE_URL}/personas",
        headers={"Authorization": f"Bearer {token}"},
    )
    personas = personas_resp.json().get("personas", [])
    persona_id = personas[0]["id"] if personas else ""
    print(f"[OK] 可用 personas: {[p['name'] for p in personas]}")

    # 3. 创建账号池条目
    payload = {
        "platform": "xhs",
        "account_id": "95476081477",
        "nickname": "开服装店的王大姐",
        "cookie": XHS_COOKIE,
        "persona": persona_id,
        "content_vertical": "宠物健康",
        "lifecycle_phase": "growth",
        "proxy_config": None,
    }

    create_resp = requests.post(
        f"{BASE_URL}/account-pool",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    if create_resp.status_code == 201:
        data = create_resp.json()
        print("=" * 60)
        print("XHS 账号已通过 API 写入账号池")
        print("=" * 60)
        print(f"  Entry ID      : {data['id']}")
        print(f"  Platform      : {data['platform']}")
        print(f"  Account ID    : {data['account_id']}")
        print(f"  Nickname      : {data['nickname']}")
        print(f"  Persona       : {data['persona']}")
        print(f"  Content V     : {data['content_vertical']}")
        print(f"  Lifecycle     : {data['lifecycle_phase']}")
        print(f"  Health Score  : {data['health_score']}")
        print(f"  Fingerprint   : {json.dumps(data['fingerprint_profile'], ensure_ascii=False)[:100]}...")
        print("=" * 60)
        print("刷新 http://localhost:5173/account-pool 即可看到该账号")
    else:
        print(f"[FAIL] 创建账号失败: {create_resp.status_code}")
        print(create_resp.text)


if __name__ == "__main__":
    main()
