"""Xiaohongshu real publisher using the `xhs` library (v0.2.13).

Integrates with XhsClient to publish image notes via creator API.
Reads per-account config (cookie, fingerprint, proxy) from the account pool.
"""

import logging
import os
import tempfile
import textwrap
from typing import Dict, List, Optional

from PIL import Image, ImageDraw, ImageFont

from src.core.config import settings

logger = logging.getLogger(__name__)

# Lazy import xhs to avoid hard dependency errors at module load time
_XHS_CLIENTS: Dict[str, object] = {}
_MAX_CLIENT_CACHE_SIZE = 50  # LRU eviction threshold


def _get_xhs_client(cookie: str, user_agent: str = "", proxies: Optional[Dict] = None):
    """Get or create an XhsClient for the given cookie.

    LRU cache with size limit to prevent memory leaks.
    Account deletion/updates should call invalidate_xhs_client_cache().
    """
    cache_key = f"{cookie[:32]}:{user_agent[:32]}"

    # LRU: move accessed key to end (most-recently-used)
    if cache_key in _XHS_CLIENTS:
        client = _XHS_CLIENTS.pop(cache_key)
        _XHS_CLIENTS[cache_key] = client
        return client

    # Evict oldest if at capacity
    while len(_XHS_CLIENTS) >= _MAX_CLIENT_CACHE_SIZE:
        oldest_key = next(iter(_XHS_CLIENTS))
        logger.debug("Evicting oldest XhsClient from cache: %s", oldest_key[:16])
        del _XHS_CLIENTS[oldest_key]

    from xhs import XhsClient
    from xhs.help import sign as _xhs_sign

    def _custom_sign(uri, data=None, a1='', web_session='', **kwargs):
        return _xhs_sign(uri, data, a1=a1)

    if not cookie:
        raise RuntimeError("Cookie is required for XhsClient")

    _XHS_CLIENTS[cache_key] = XhsClient(
        cookie=cookie,
        user_agent=user_agent or None,
        sign=_custom_sign,
        proxies=proxies,
    )
    logger.info("XhsClient created (cache_key=%s, ua=%s, proxies=%s)", cache_key[:16], bool(user_agent), bool(proxies))
    return _XHS_CLIENTS[cache_key]


def invalidate_xhs_client_cache(cookie: str = "", user_agent: str = "") -> None:
    """Invalidate cached XhsClient for a specific account.

    Call this when an account's cookie or proxy config is updated/deleted.
    If cookie is empty, clears the entire cache.
    """
    global _XHS_CLIENTS
    if not cookie:
        evicted = len(_XHS_CLIENTS)
        _XHS_CLIENTS.clear()
        logger.info("Cleared all %d XhsClient cache entries", evicted)
        return
    cache_key = f"{cookie[:32]}:{user_agent[:32]}"
    if cache_key in _XHS_CLIENTS:
        del _XHS_CLIENTS[cache_key]
        logger.info("Invalidated XhsClient cache for key %s", cache_key[:16])


def _load_font(size: int = 48):
    """Load a Chinese-capable font or fallback to default."""
    candidates = [
        "/c/Windows/Fonts/msyh.ttc",
        "/c/Windows/Fonts/simhei.ttf",
        "/c/Windows/Fonts/simsun.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _generate_placeholder_image(title: str, output_path: str) -> str:
    """Generate a 3:4 placeholder image with title text (XHS-friendly ratio)."""
    width, height = 900, 1200
    bg_color = (255, 36, 66)  # XHS brand red
    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    font_large = _load_font(64)
    font_small = _load_font(32)

    # Title text wrapping
    max_chars_per_line = 12
    lines = textwrap.wrap(title, width=max_chars_per_line) if title else ["小红书笔记"]
    if not lines:
        lines = ["小红书笔记"]

    # Calculate vertical centering
    line_height = 80
    total_text_height = len(lines) * line_height + 60  # +60 for subtitle
    start_y = (height - total_text_height) // 2

    # Draw title lines
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font_large)
        text_w = bbox[2] - bbox[0]
        x = (width - text_w) // 2
        y = start_y + i * line_height
        draw.text((x, y), line, fill=(255, 255, 255), font=font_large)

    # Draw subtitle
    subtitle = "EcoDreamOmni · AI 生成"
    bbox = draw.textbbox((0, 0), subtitle, font=font_small)
    text_w = bbox[2] - bbox[0]
    x = (width - text_w) // 2
    y = start_y + len(lines) * line_height + 20
    draw.text((x, y), subtitle, fill=(255, 220, 220), font=font_small)

    img.save(output_path, "JPEG", quality=90)
    return output_path


def _resolve_topics(client, tags: List[str]) -> List[dict]:
    """Resolve tag strings to XHS topic dicts via get_suggest_topic."""
    topics: List[dict] = []
    for tag in tags:
        try:
            results = client.get_suggest_topic(tag)
            if results:
                t = results[0]
                topics.append(
                    {
                        "id": t.get("id", ""),
                        "name": t.get("name", tag),
                        "type": "topic",
                        "link": t.get("link", ""),
                    }
                )
        except Exception as exc:
            logger.debug("Failed to resolve topic for tag %r: %s", tag, exc)
    return topics


def _extract_xhs_error(exc) -> str:
    """Extract human-readable error message from xhs DataFetchError.

    The xhs library uses ``response.json()`` which may mis-decode UTF-8
    bytes on some platforms. We re-parse the raw bytes to recover the
    original message.
    """
    import json

    # Known error code mappings (reverse-engineered from xhs API)
    _ERROR_MAP = {
        -102: "账号异常（禁言/风控）",
        -9150: "请求参数错误",
        -9042: "账号功能受限（需绑定手机/实名认证/新号风控）",
    }

    try:
        # Case 1: exception has raw response object
        if hasattr(exc, "response") and exc.response is not None:
            raw = exc.response.content
            data = json.loads(raw.decode("utf-8"))
            err_msg = data.get("msg", "")
            result_code = data.get("result", data.get("code", ""))

            desc = _ERROR_MAP.get(result_code, f"错误码 {result_code}")
            if err_msg:
                return f"{desc}: {err_msg}"
            return desc
    except Exception:
        pass

    try:
        # Case 2: exception args contain a dict (xhs library DataFetchError)
        if hasattr(exc, "args") and exc.args and isinstance(exc.args[0], dict):
            data = exc.args[0]
            err_msg = data.get("msg", "")
            result_code = data.get("result", data.get("code", ""))
            desc = _ERROR_MAP.get(result_code, f"错误码 {result_code}")
            if err_msg:
                return f"{desc}: {err_msg}"
            return desc
    except Exception:
        pass

    return str(exc)


def check_account_status(cookie: str) -> Dict:
    """Check whether the given XHS account can publish.

    Returns:
        {"healthy": bool, "reason": str, "user_id": str, "nickname": str}
    """
    try:
        client = _get_xhs_client(cookie)
        info = client.get_self_info2()
        user_id = info.get("user_id", "")
        nickname = info.get("nickname", "")

        # Probe actual publishing capability with a private test note
        import tempfile
        from PIL import Image

        img = Image.new("RGB", (100, 100), color=(255, 36, 66))
        fd, path = tempfile.mkstemp(suffix=".jpg")
        os.close(fd)
        img.save(path)

        try:
            client.create_image_note(
                title="",
                desc="",
                files=[path],
                is_private=True,
            )
            return {
                "healthy": True,
                "reason": "",
                "user_id": user_id,
                "nickname": nickname,
            }
        except Exception as exc:
            err = _extract_xhs_error(exc)
            if "-9150" in err or "参数错误" in err or "标题" in err:
                return {
                    "healthy": True,
                    "reason": "",
                    "user_id": user_id,
                    "nickname": nickname,
                }
            return {
                "healthy": False,
                "reason": err,
                "user_id": user_id,
                "nickname": nickname,
            }
        finally:
            try:
                os.remove(path)
            except Exception:
                pass
    except Exception as exc:
        return {
            "healthy": False,
            "reason": f"无法获取账号信息: {exc}",
            "user_id": "",
            "nickname": "",
        }


def _download_image(url: str, output_path: str) -> bool:
    """Download remote image to local path."""
    try:
        import httpx
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(resp.content)
        return True
    except Exception as exc:
        logger.warning("Failed to download image %s: %s", url, exc)
        return False


def publish_to_xhs(account_id: str, content: Dict) -> Dict:
    """Publish content to Xiaohongshu via xhs library.

    Args:
        account_id: Account pool entry ID to read cookie/fingerprint/proxy from.
        content: {
            "title": str,
            "body": str,
            "tags": List[str],
            "images": Optional[List[str]],  # local file paths
            "cover_image_url": Optional[str],  # remote URL fallback
        }

    Returns:
        {"success": bool, "platform_post_id": str, "published_url": str, "error": str}
    """
    # ── 1. Resolve per-account config from account pool ──
    from src.models.account_pool import get_pool_entry
    from src.services.proxy_service import build_requests_proxies, get_proxy, record_proxy_result

    # Resolve per-account config from account pool
    cookie = ""
    user_agent = ""
    proxies = None
    proxy_id = ""

    account = get_pool_entry(account_id)
    if account is None:
        logger.warning("Account %s not found in pool, falling back to global cookie", account_id)
        cookie = settings.REDNOTE_COOKIE
    else:
        cookie = account.cookie
        # P0 Fix: Detect placeholder cookies and fallback to global real cookie
        if not cookie or cookie in ("demo_cookie", "", "placeholder"):
            logger.warning(
                "Account %s has placeholder cookie (%r), falling back to REDNOTE_COOKIE",
                account_id, cookie,
            )
            cookie = settings.REDNOTE_COOKIE
        fp = account.fingerprint_profile
        user_agent = fp.user_agent if fp else ""

        # Resolve proxy
        if account.proxy_config and account.proxy_config.proxy_id:
            proxy_id = account.proxy_config.proxy_id
            proxy_entry = get_proxy(proxy_id)
            if proxy_entry and proxy_entry.is_active:
                try:
                    proxies = build_requests_proxies(proxy_entry)
                    logger.info("Using proxy %s for account %s", proxy_id, account_id)
                except Exception as exc:
                    logger.warning("Failed to build proxy %s: %s", proxy_id, exc)
            else:
                logger.warning("Proxy %s not found or inactive for account %s", proxy_id, account_id)

    title = content.get("title", "")
    body = content.get("body", "")
    tags = content.get("tags", []) or []
    images = content.get("images", []) or []
    cover_image_url = content.get("cover_image_url", "")

    if not title or not body:
        return {
            "success": False,
            "platform": "xhs",
            "platform_post_id": "",
            "published_url": "",
            "error": "Content title and body are required",
        }

    if not cookie:
        return {
            "success": False,
            "platform": "xhs",
            "platform_post_id": "",
            "published_url": "",
            "error": "REDNOTE_COOKIE not configured and account has no cookie",
        }

    # ── 2. Resolve images: local paths first, then download cover_image_url fallback ──
    temp_paths: List[str] = []
    if not images and cover_image_url:
        # Download remote cover image
        fd, temp_path = tempfile.mkstemp(suffix=".jpg")
        os.close(fd)
        if _download_image(cover_image_url, temp_path):
            images = [temp_path]
            temp_paths.append(temp_path)
            logger.warning("Downloaded cover image: %s -> %s", cover_image_url, temp_path)
        else:
            # Clean up failed download temp file
            try:
                os.remove(temp_path)
            except Exception:
                pass

    # ── 3. Initialise XhsClient with per-account settings ──
    try:
        client = _get_xhs_client(cookie=cookie, user_agent=user_agent, proxies=proxies)
    except Exception as exc:
        logger.error("XhsClient initialization failed: %s", exc)
        return {
            "success": False,
            "platform": "xhs",
            "platform_post_id": "",
            "published_url": "",
            "error": f"XhsClient init failed: {exc}",
        }

    # Append tags to body in XHS hashtag format
    for tag in tags:
        body += f" #{tag}[话题]#"

    # Resolve topics metadata
    topics = _resolve_topics(client, tags)

    # Prepare images: use provided paths, download remote URL, or generate placeholder
    if images:
        # Validate local image paths exist
        valid_images = [p for p in images if os.path.exists(p)]
        if not valid_images:
            return {
                "success": False,
                "platform": "xhs",
                "platform_post_id": "",
                "published_url": "",
                "error": "No valid image files found",
            }
        images = valid_images
    elif not images and not temp_paths:
        # No images at all — generate placeholder as last resort
        fd, temp_path = tempfile.mkstemp(suffix=".jpg")
        os.close(fd)
        _generate_placeholder_image(title, temp_path)
        images = [temp_path]
        temp_paths.append(temp_path)
        logger.info("Generated placeholder image: %s", temp_path)

    try:
        result = client.create_image_note(
            title=title,
            desc=body,
            files=images,
            topics=topics,
            is_private=False,
        )

        logger.info("XHS publish result: %s", result)

        # result is a dict like {"note_id": "...", "note_url": "..."} or similar
        note_id = ""
        if isinstance(result, dict):
            note_id = result.get("note_id", "")
            if not note_id:
                # Some versions may return under different keys
                note_id = result.get("id", "")

        published_url = f"https://www.xiaohongshu.com/explore/{note_id}" if note_id else ""

        if proxy_id:
            record_proxy_result(proxy_id, success=True)

        return {
            "success": True,
            "platform": "xhs",
            "platform_post_id": note_id,
            "published_url": published_url,
            "error": "",
        }

    except Exception as exc:
        logger.exception("XHS publish failed")
        error_msg = _extract_xhs_error(exc)
        if proxy_id:
            record_proxy_result(proxy_id, success=False)
        return {
            "success": False,
            "platform": "xhs",
            "platform_post_id": "",
            "published_url": "",
            "error": error_msg,
        }

    finally:
        for tp in temp_paths:
            try:
                os.remove(tp)
            except Exception:
                pass
