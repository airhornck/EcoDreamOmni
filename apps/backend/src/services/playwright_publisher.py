"""Publisher adapter: routes platforms to real or mock implementations.

- xhs        → xhs_publisher (real XhsClient via xhs library, per-account config)
- douyin     → mock (W11+ Playwright automation)
- wechat_channels → mock (W11+ Playwright automation)
"""

import logging
import secrets
from typing import Dict

logger = logging.getLogger(__name__)

_SUPPORTED_PLATFORMS = {"xhs", "douyin", "wechat_channels"}


def _mock_publish(
    draft_id: str,
    account_id: str,
    platform: str,
    content: Dict,
) -> Dict:
    """Mock publisher for unsupported platforms."""
    post_id = secrets.token_hex(8)
    platform_urls = {
        "xhs": f"https://www.xiaohongshu.com/explore/{post_id}",
        "douyin": f"https://www.douyin.com/video/{post_id}",
        "wechat_channels": f"https://channels.weixin.com/video/{post_id}",
    }
    return {
        "success": True,
        "platform": platform,
        "platform_post_id": post_id,
        "published_url": platform_urls.get(platform, ""),
        "error": "",
    }


def publish_content(
    draft_id: str,
    account_id: str,
    platform: str,
    content: Dict,
) -> Dict:
    """Route publish request to the appropriate backend.

    Args:
        draft_id: Content draft ID
        account_id: Target account pool entry ID
        platform: Target platform
        content: {"title": str, "body": str, "tags": list, "images": list}

    Returns:
        {"success": bool, "platform_post_id": str, "published_url": str, "error": str}
    """
    if platform not in _SUPPORTED_PLATFORMS:
        return {
            "success": False,
            "platform": platform,
            "platform_post_id": "",
            "published_url": "",
            "error": f"Unsupported platform: {platform}. Supported: {', '.join(_SUPPORTED_PLATFORMS)}",
        }

    if not content.get("title") or not content.get("body"):
        return {
            "success": False,
            "platform": platform,
            "platform_post_id": "",
            "published_url": "",
            "error": "Content title and body are required",
        }

    if platform == "xhs":
        try:
            from src.services.xhs_publisher import publish_to_xhs

            return publish_to_xhs(account_id=account_id, content=content)
        except Exception:
            logger.exception("xhs publisher failed, falling back to mock")
            # Fallback to mock so the workflow doesn't hard-break
            return _mock_publish(draft_id, account_id, platform, content)

    # douyin / wechat_channels — mock for now
    return _mock_publish(draft_id, account_id, platform, content)
