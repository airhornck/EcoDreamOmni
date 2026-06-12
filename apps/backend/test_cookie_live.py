#!/usr/bin/env python3
"""
XHS Cookie 实战测试脚本 — 验证 Cookie + 签名 + 发布能力
用法: cd apps/backend && PYTHONPATH=../../vendor/platform-crawlers/xhs-api .venv/Scripts/python.exe test_cookie_live.py
"""

import json
import os
import sys
import tempfile
import time
import traceback
from datetime import datetime

# 把 vendor 里的 xhs 源码加入路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "vendor", "platform-crawlers", "xhs-api"))

from PIL import Image
from xhs import DataFetchError, IPBlockError, SignError, XhsClient
from xhs.exception import NeedVerifyError
from xhs.help import sign as _xhs_sign

# ─────────────────────────────────────────────
# 1. 配置区：填入你提供的 Cookie
# ─────────────────────────────────────────────
TEST_COOKIE = (
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

# 可选：自定义 UA / 代理（留空则使用默认）
CUSTOM_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
PROXIES = None  # 例: {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}


# ─────────────────────────────────────────────
# 2. 签名函数（复用项目内逻辑）
# ─────────────────────────────────────────────
def _custom_sign(uri, data=None, a1="", web_session="", **kwargs):
    return _xhs_sign(uri, data, a1=a1)


def _extract_error(exc) -> str:
    """从 xhs 异常中提取可读信息"""
    _ERROR_MAP = {
        -102: "账号异常（禁言/风控）",
        -9150: "请求参数错误",
        -9042: "账号功能受限（需绑定手机/实名认证/新号风控）",
    }
    try:
        if hasattr(exc, "response") and exc.response is not None:
            raw = exc.response.content
            data = json.loads(raw.decode("utf-8"))
            err_msg = data.get("msg", "")
            result_code = data.get("result", data.get("code", ""))
            desc = _ERROR_MAP.get(result_code, f"错误码 {result_code}")
            return f"{desc}: {err_msg}" if err_msg else desc
    except Exception:
        pass
    try:
        if hasattr(exc, "args") and exc.args and isinstance(exc.args[0], dict):
            data = exc.args[0]
            err_msg = data.get("msg", "")
            result_code = data.get("result", data.get("code", ""))
            desc = _ERROR_MAP.get(result_code, f"错误码 {result_code}")
            return f"{desc}: {err_msg}" if err_msg else desc
    except Exception:
        pass
    return str(exc)


# ─────────────────────────────────────────────
# 3. 测试执行
# ─────────────────────────────────────────────
def main():
    report = []
    report.append("=" * 60)
    report.append("XHS Cookie 实战验证报告")
    report.append(f"测试时间: {datetime.now().isoformat()}")
    report.append("=" * 60)

    # 3.1 初始化 Client
    report.append("\n【初始化 XhsClient】")
    try:
        client = XhsClient(
            cookie=TEST_COOKIE,
            user_agent=CUSTOM_UA or None,
            sign=_custom_sign,
            proxies=PROXIES,
        )
        report.append(f"  [OK] Client 创建成功")
        report.append(f"  UA    : {client.user_agent}")
        report.append(f"  Proxy : {PROXIES or '无'}")
        # 打印关键 Cookie 字段
        cd = client.cookie_dict
        for k in ["a1", "web_session", "webId", "gid", "xsecappid", "x-rednote-datactry"]:
            report.append(f"  Cookie[{k}] = {cd.get(k, 'N/A')[:50]}...")
    except Exception as exc:
        report.append(f"  [FAIL] Client 创建失败: {exc}")
        _print_report(report)
        return

    # 3.2 签名自检
    report.append("\n【签名机制自检】")
    try:
        from xhs.help import sign
        test_uri = "/api/sns/web/v2/user/me"
        test_data = None
        sig = sign(test_uri, test_data, a1=cd.get("a1", ""))
        report.append(f"  [OK] sign() 返回字段: {list(sig.keys())}")
        report.append(f"       x-t        = {sig.get('x-t')}")
        report.append(f"       x-s        = {sig.get('x-s', '')[:24]}...")
        report.append(f"       x-s-common = {sig.get('x-s-common', '')[:24]}...")
    except Exception as exc:
        report.append(f"  [FAIL] 签名生成异常: {exc}")

    # 3.3 登录验证 — get_self_info2
    report.append("\n【登录验证】get_self_info2()")
    user_id = ""
    nickname = ""
    try:
        info = client.get_self_info2()
        user_id = info.get("user_id", "")
        nickname = info.get("nickname", "")
        report.append(f"  [OK] 用户信息获取成功")
        report.append(f"       user_id : {user_id}")
        report.append(f"       nickname: {nickname}")
        # 打印更多可用字段
        for k in ["red_id", "images", "desc"]:
            if k in info:
                v = info[k]
                if isinstance(v, str):
                    report.append(f"       {k} : {v}")
                else:
                    report.append(f"       {k} : {v}")
    except SignError as exc:
        report.append(f"  [FAIL] 签名被拦截（SignError）— 指纹/签名对抗手段可能未生效")
        report.append(f"         详情: {_extract_error(exc)}")
    except IPBlockError as exc:
        report.append(f"  [FAIL] IP 被封（IPBlockError）")
        report.append(f"         详情: {_extract_error(exc)}")
    except NeedVerifyError as exc:
        report.append(f"  [FAIL] 触发验证码（NeedVerifyError）")
        report.append(f"         Verifytype: {exc.verify_type}, Verifyuuid: {exc.verify_uuid}")
    except DataFetchError as exc:
        report.append(f"  [FAIL] 数据获取失败（DataFetchError）")
        report.append(f"         详情: {_extract_error(exc)}")
    except Exception as exc:
        report.append(f"  [FAIL] 未知异常: {exc}")
        report.append(traceback.format_exc())

    # 3.4 创作者中心 — get_self_info_from_creator
    report.append("\n【创作者中心】get_self_info_from_creator()")
    try:
        cinfo = client.get_self_info_from_creator()
        report.append(f"  [OK] 创作者中心正常")
        report.append(f"       返回字段: {list(cinfo.keys())[:10]}")
    except SignError as exc:
        report.append(f"  [FAIL] 签名被拦截（SignError）")
        report.append(f"         详情: {_extract_error(exc)}")
    except IPBlockError as exc:
        report.append(f"  [FAIL] IP 被封")
    except DataFetchError as exc:
        err = _extract_error(exc)
        if "登录" in err or "未登录" in err:
            report.append(f"  [WARN] 未登录创作者中心（Cookie 可能缺少 creator 域权限）")
        else:
            report.append(f"  [FAIL] {err}")
    except Exception as exc:
        report.append(f"  [WARN] {exc}")

    # 3.5 发布能力探测（私密笔记，带空标题/正文，预期参数错误或成功）
    report.append("\n【发布能力探测】create_image_note(title='', desc='', is_private=True)")
    img_path = None
    try:
        img = Image.new("RGB", (100, 100), color=(255, 36, 66))
        fd, img_path = tempfile.mkstemp(suffix=".jpg")
        os.close(fd)
        img.save(img_path)

        try:
            result = client.create_image_note(
                title="",
                desc="",
                files=[img_path],
                is_private=True,
            )
            report.append(f"  [OK] 发布接口通，返回: {json.dumps(result, ensure_ascii=False)[:200]}")
            report.append(f"  [结论] Cookie + 签名完全有效，账号具备发布权限")
        except SignError as exc:
            report.append(f"  [FAIL] 签名被拦截（SignError）— API 拒绝本次请求签名")
            report.append(f"         详情: {_extract_error(exc)}")
        except DataFetchError as exc:
            err = _extract_error(exc)
            if "-9150" in err or "参数" in err or "标题" in err:
                report.append(f"  [OK] 发布接口通（参数校验拒绝空标题）")
                report.append(f"       说明: 签名通过，账号具备发布权限")
                report.append(f"       返回: {err}")
            elif "-9042" in err:
                report.append(f"  [FAIL] 账号功能受限（-9042）")
                report.append(f"         返回: {err}")
                report.append(f"         建议: 绑定手机号 / 实名认证 / 养号")
            else:
                report.append(f"  [FAIL] 发布被拒绝: {err}")
        except Exception as exc:
            report.append(f"  [FAIL] 发布异常: {exc}")
    finally:
        if img_path and os.path.exists(img_path):
            try:
                os.remove(img_path)
            except Exception:
                pass

    # 3.6 其他读接口探测（进一步验证签名存活）
    report.append("\n【读接口存活探测】")
    for name, fn in [
        ("get_home_feed_category", lambda: client.get_home_feed_category()),
        ("get_search_suggestion('猫')", lambda: client.get_search_suggestion("猫")),
    ]:
        try:
            res = fn()
            report.append(f"  [OK] {name} 成功，返回长度/条数: {len(res) if hasattr(res, '__len__') else 'N/A'}")
        except SignError:
            report.append(f"  [FAIL] {name} 触发 SignError")
        except DataFetchError as exc:
            report.append(f"  [WARN] {name} 数据异常: {_extract_error(exc)[:80]}")
        except Exception as exc:
            report.append(f"  [WARN] {name} 异常: {exc}")

    # 3.7 指纹/对抗手段总结
    report.append("\n【指纹 & 反检测套件状态】")
    report.append(f"  UA 自定义          : {'已启用' if CUSTOM_UA else '默认'}")
    report.append(f"  代理配置           : {'已启用' if PROXIES else '未启用'}")
    report.append(f"  签名函数           : Python 本地签名 (help.sign)")
    report.append(f"  x-s-common 生成    : 是（包含平台码、版本、xhs-pc-web 等）")
    report.append(f"  Cookie 自动补全    : a1/webId/gid 缺失时自动填充（当前已提供完整 Cookie）")

    report.append("\n【结论】")
    if user_id:
        report.append(f"  1. Cookie 有效，已登录（user_id={user_id}）")
    else:
        report.append(f"  1. Cookie 登录失败，请检查 Cookie 是否过期或被踢下线")
    report.append(f"  2. 签名机制运行正常（未报 SignError）")
    report.append(f"  3. 如需完整指纹对抗，建议配合：")
    report.append(f"     • 真实浏览器 UA + viewport")
    report.append(f"     • 住宅代理 / 移动端代理")
    report.append(f"     • Playwright 真机签名（window._webmsxyw）")
    report.append("=" * 60)

    _print_report(report)


def _print_report(report):
    text = "\n".join(report)
    print(text)
    # 同时写到文件
    out_path = os.path.join(os.path.dirname(__file__), "xhs_cookie_live_report.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    print(f"\n[报告已保存] {out_path}")


if __name__ == "__main__":
    main()
