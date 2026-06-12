#!/usr/bin/env python3
"""将测试通过的 XHS Cookie 直接写入账号池内存数据库."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.services.account_pool_service import create_account
from src.services.persona_pool import list_personas

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
    personas = list_personas()
    print(f"可用 Personas: {[p.name for p in personas]}")

    # 选择第一个可用 persona，如果没有则留空
    persona_id = personas[0].id if personas else ""

    entry = create_account(
        platform="xhs",
        account_id="95476081477",
        nickname="开服装店的王大姐",
        cookie=XHS_COOKIE,
        persona=persona_id,
        content_vertical="宠物健康",
        lifecycle_phase="growth",
        fingerprint_profile=None,  # 自动生成
        proxy_config=None,
    )

    print("=" * 60)
    print("XHS 账号已写入账号池")
    print("=" * 60)
    print(f"  Entry ID      : {entry.id}")
    print(f"  Platform      : {entry.platform}")
    print(f"  Account ID    : {entry.account_id}")
    print(f"  Nickname      : {entry.nickname}")
    print(f"  Persona       : {entry.persona}")
    print(f"  Content V     : {entry.content_vertical}")
    print(f"  Lifecycle     : {entry.lifecycle_phase}")
    print(f"  Health Score  : {entry.health_score}")
    print(f"  Fingerprint UA: {entry.fingerprint_profile.user_agent}")
    print(f"  Cookie (前80字符): {entry.cookie[:80]}...")
    print("=" * 60)
    print("刷新 http://localhost:5173/account-pool 即可看到该账号")


if __name__ == "__main__":
    main()
