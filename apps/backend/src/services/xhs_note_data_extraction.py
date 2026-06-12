"""Xiaohongshu note engagement data extraction service.

24h post-publish data recovery for the DataAnalyst feedback loop.
MVP: Uses get_user_notes() (no xsec_token required) to fetch interact_info.
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def _extract_user_id(self_info: dict) -> Optional[str]:
    """Extract user_id from get_self_info2() response."""
    try:
        # Response format varies; try common paths
        data = self_info.get("data", {})
        if "user_id" in data:
            return str(data["user_id"])
        if "id" in data:
            return str(data["id"])
        # Nested paths
        user = data.get("user", {})
        if "user_id" in user:
            return str(user["user_id"])
        return None
    except Exception:
        return None


def _parse_interact_info(interact: dict) -> dict:
    """Parse interact_info dict into standard metrics."""
    return {
        "likes": _to_int(interact.get("liked_count")),
        "comments": _to_int(interact.get("comment_count")),
        "saves": _to_int(interact.get("collected_count")),
        "shares": _to_int(interact.get("share_count")),
        "views": _to_int(interact.get("view_count")),
    }


def _to_int(val) -> Optional[int]:
    """Safely convert a value to int or None."""
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def fetch_note_engagement(ctx: Dict) -> Dict:
    """Fetch engagement metrics for a published XHS note.

    Input context:
        - account_id: str
        - platform_post_id: str (note_id)

    Returns:
        {
            "success": bool,
            "metrics": {"likes": int|None, "comments": int|None, "saves": int|None,
                        "shares": int|None, "views": int|None},
            "error": str|None,
        }
    """
    account_id = ctx.get("account_id")
    note_id = ctx.get("platform_post_id")

    if not account_id:
        return {"success": False, "metrics": {}, "error": "Missing account_id"}
    if not note_id:
        return {"success": False, "metrics": {}, "error": "Missing platform_post_id"}

    # Load account config
    from src.models.account_pool import get_pool_entry

    account = get_pool_entry(account_id)
    if not account:
        return {"success": False, "metrics": {}, "error": f"Account {account_id} not found"}

    # Check feature toggle (PRD: default off)
    if not getattr(account, "auto_engagement_fetch", False):
        return {
            "success": False,
            "metrics": {},
            "error": "Auto engagement fetch is disabled for this account",
        }

    # Initialize XHS client (reuses cached clients from xhs_publisher)
    from src.services.xhs_publisher import _get_xhs_client

    try:
        client = _get_xhs_client(
            cookie=account.cookie,
            user_agent=account.fingerprint_profile.user_agent if account.fingerprint_profile else "",
            proxies=account.proxy_config.to_dict() if getattr(account, "proxy_config", None) else None,
        )
    except Exception as exc:
        logger.error("XHS client init failed: %s", exc)
        return {"success": False, "metrics": {}, "error": f"XHS client init failed: {exc}"}

    # ── Strategy 1: user notes list (no xsec_token, single API call) ──
    try:
        self_info = client.get_self_info2()
        user_id = _extract_user_id(self_info)
        if not user_id:
            raise ValueError("Could not extract user_id from get_self_info2")

        notes_result = client.get_user_notes(user_id)
        notes = notes_result.get("notes", [])

        for note in notes:
            if note.get("note_id") == note_id:
                interact = note.get("interact_info", {})
                metrics = _parse_interact_info(interact)
                logger.info(
                    "Fetched engagement for note %s: likes=%s comments=%s saves=%s",
                    note_id,
                    metrics.get("likes"),
                    metrics.get("comments"),
                    metrics.get("saves"),
                )
                return {"success": True, "metrics": metrics, "error": None}

        # Note not in recent 30 — may need pagination or different strategy
        raise ValueError(f"Note {note_id} not found in recent notes list")

    except Exception as exc:
        logger.warning("Strategy 1 (user notes list) failed: %s", exc)

    # ── Strategy 2: creator note statistics (is_creator endpoint) ──
    try:
        stats = client.get_notes_statistics(time=1, is_recent=True, page_size=48)
        items = stats.get("data", {}).get("items", [])
        for item in items:
            if item.get("note_id") == note_id or item.get("id") == note_id:
                metrics = {
                    "likes": _to_int(item.get("liked_count")),
                    "comments": _to_int(item.get("comment_count")),
                    "saves": _to_int(item.get("collected_count")),
                    "shares": _to_int(item.get("share_count")),
                    "views": _to_int(item.get("view_count")),
                }
                return {"success": True, "metrics": metrics, "error": None}
        raise ValueError(f"Note {note_id} not found in creator statistics")
    except Exception as exc:
        logger.warning("Strategy 2 (creator statistics) failed: %s", exc)

    # All strategies exhausted
    return {
        "success": False,
        "metrics": {},
        "error": "Failed to fetch note engagement: all strategies exhausted",
    }
