"""Service connectivity test — LLM, Image Gen, Proxy."""

import asyncio
import json
import sys
from pathlib import Path

# Load env
import os
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key, val)

import httpx


# ─── 1. Test DeepSeek LLM ───
async def test_llm():
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    model = os.environ.get("DEFAULT_LLM_MODEL", "deepseek-chat")
    if not api_key:
        return "SKIP", "DEEPSEEK_API_KEY not set"

    url = "https://api.deepseek.com/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Say 'OK' only"}],
        "max_tokens": 10,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(url, headers=headers, json=payload)
            if r.status_code == 200:
                data = r.json()
                content = data["choices"][0]["message"]["content"]
                return "PASS", f"model={model}, response='{content.strip()[:50]}'"
            else:
                return "FAIL", f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return "FAIL", str(e)


# ─── 2. Test Qwen Image Generation ───
async def test_image_gen():
    api_key = os.environ.get("QWEN_IMAGE_API_KEY", "")
    model = os.environ.get("QWEN_IMAGE_MODEL", "qwen-image-2.0-pro")
    if not api_key:
        return "SKIP", "QWEN_IMAGE_API_KEY not set"

    # Qwen image API (DashScope)
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
    payload = {
        "model": model,
        "input": {"prompt": "a cute cat sitting on a sofa, realistic photo"},
        "parameters": {"size": "1024*1024", "n": 1},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable",
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(url, headers=headers, json=payload)
            if r.status_code in (200, 202):
                data = r.json()
                task_id = data.get("output", {}).get("task_id", "N/A")
                return "PASS", f"model={model}, task_id={task_id}"
            else:
                return "FAIL", f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return "FAIL", str(e)


# ─── 3. Test Residential Proxy ───
async def test_proxy():
    host = os.environ.get("PROXY_HTTP_HOST", "")
    port = int(os.environ.get("PROXY_HTTP_PORT", "0"))
    user = os.environ.get("PROXY_HTTP_USER", "")
    pwd = os.environ.get("PROXY_HTTP_PASS", "")

    if not host or not port:
        return "SKIP", "PROXY_HTTP_HOST/PORT not set"

    proxy_url = f"http://{user}:{pwd}@{host}:{port}" if user else f"http://{host}:{port}"
    proxies = {"http://": proxy_url, "https://": proxy_url}

    try:
        proxy_arg = proxy_url if user else None
        async with httpx.AsyncClient(timeout=30, proxy=proxy_arg) as client:
            r = await client.get("https://httpbin.org/ip")
            if r.status_code == 200:
                data = r.json()
                origin = data.get("origin", "unknown")
                return "PASS", f"proxy={host}:{port}, origin_ip={origin}"
            else:
                return "FAIL", f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return "FAIL", str(e)


async def main():
    print("=" * 60)
    print("EcoDream Omni Service Connectivity Test")
    print("=" * 60)

    results = []

    print("\n[1/3] Testing DeepSeek LLM ...")
    status, msg = await test_llm()
    results.append(("LLM (DeepSeek)", status, msg))
    print(f"  Status: {status} — {msg}")

    print("\n[2/3] Testing Qwen Image Generation ...")
    status, msg = await test_image_gen()
    results.append(("Image Gen (Qwen)", status, msg))
    print(f"  Status: {status} — {msg}")

    print("\n[3/3] Testing Residential Proxy ...")
    status, msg = await test_proxy()
    results.append(("Proxy (HTTP)", status, msg))
    print(f"  Status: {status} — {msg}")

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    for name, status, msg in results:
        icon = "✅" if status == "PASS" else ("⚠️ " if status == "SKIP" else "❌")
        print(f"{icon} {name}: {status}")
    print("=" * 60)

    fail_count = sum(1 for _, s, _ in results if s == "FAIL")
    return 1 if fail_count > 0 else 0


if __name__ == "__main__":
    code = asyncio.run(main())
    sys.exit(code)
