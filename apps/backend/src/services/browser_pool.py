"""Browser pool for Playwright context isolation with rebrowser-patches support."""

import os
from typing import Dict, Optional

# Set rebrowser-patches environment defaults before any Playwright import
os.environ.setdefault("REBROWSER_PATCHES_RUNTIME_FIX_MODE", "addBinding")
os.environ.setdefault("REBROWSER_PATCHES_UTILITY_WORLD_NAME", "util")


class BrowserPool:
    """MVP: Browser context tracking and config builder.

    Full Playwright integration (browser.launch + new_context) will be
    wired in W7 Publisher when actual publishing starts.
    """

    def __init__(self):
        self._active_contexts: set[str] = set()
        self._launched_count: int = 0

    @property
    def active_contexts(self) -> set[str]:
        return self._active_contexts.copy()

    @property
    def launched_count(self) -> int:
        return self._launched_count

    def mark_launched(self, context_id: str) -> None:
        self._active_contexts.add(context_id)
        self._launched_count += 1

    def mark_closed(self, context_id: str) -> None:
        self._active_contexts.discard(context_id)

    def is_active(self, context_id: str) -> bool:
        return context_id in self._active_contexts


def build_context_config(fingerprint: dict, proxy: Optional[dict] = None) -> dict:
    """Build Playwright BrowserContext config from fingerprint + proxy.

    Returns a dict matching playwright.Browser.new_context(**kwargs).
    """
    config = {
        "user_agent": fingerprint["user_agent"],
        "viewport": fingerprint["viewport"],
        "locale": fingerprint["locale"],
        "timezone_id": fingerprint["timezone"],
        "bypass_csp": True,
        "accept_downloads": False,
    }

    if proxy:
        # Build real proxy config from proxy service entry
        protocol = proxy.get("protocol", "http")
        host = proxy.get("host", "")
        port = proxy.get("port", 8080)
        username = proxy.get("username", "")
        password = proxy.get("password", "")

        proxy_config: Dict[str, str] = {"server": f"{protocol}://{host}:{port}"}
        if username:
            proxy_config["username"] = username
        if password:
            proxy_config["password"] = password

        config["proxy"] = proxy_config

    return config
