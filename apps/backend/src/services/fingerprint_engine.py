"""Fingerprint differentiation engine: generates unique browser fingerprints."""

import random
from typing import Dict

# Realistic viewport pools by device category
_MOBILE_VIEWPORTS = [
    {"width": 390, "height": 844},   # iPhone 14
    {"width": 393, "height": 852},   # iPhone 14 Pro
    {"width": 360, "height": 780},   # iPhone 12 mini
    {"width": 414, "height": 896},   # iPhone 11 Pro Max
]

_DESKTOP_VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 2560, "height": 1440},
    {"width": 1366, "height": 768},
    {"width": 1440, "height": 900},
    {"width": 1536, "height": 864},
    {"width": 1280, "height": 800},
]

_TABLET_VIEWPORTS = [
    {"width": 820, "height": 1180},   # iPad Air
    {"width": 768, "height": 1024},   # iPad
    {"width": 834, "height": 1194},   # iPad Pro 11
]

_USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.2420.81",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 14; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
]

_LOCALES = ["zh-CN", "zh-TW", "en-US", "ja-JP", "ko-KR"]
_TIMEZONES = ["Asia/Shanghai", "Asia/Taipei", "Asia/Tokyo", "Asia/Seoul", "America/New_York"]


def generate_fingerprint() -> Dict:
    """Generate a random but realistic browser fingerprint profile."""
    # Weighted random: mobile > desktop > tablet
    category = random.choices(
        ["mobile", "desktop", "tablet"],
        weights=[0.5, 0.4, 0.1],
        k=1,
    )[0]

    if category == "mobile":
        viewport = random.choice(_MOBILE_VIEWPORTS)
    elif category == "desktop":
        viewport = random.choice(_DESKTOP_VIEWPORTS)
    else:
        viewport = random.choice(_TABLET_VIEWPORTS)

    # Filter user agents roughly matching the viewport category
    if category == "mobile":
        ua_pool = [ua for ua in _USER_AGENTS if "Mobile" in ua and "iPad" not in ua]
    elif category == "tablet":
        ua_pool = [ua for ua in _USER_AGENTS if "iPad" in ua]
    else:
        ua_pool = [ua for ua in _USER_AGENTS if "Mobile" not in ua]

    if not ua_pool:
        ua_pool = _USER_AGENTS

    return {
        "user_agent": random.choice(ua_pool),
        "viewport": viewport,
        "locale": random.choice(_LOCALES),
        "timezone": random.choice(_TIMEZONES),
        # NOTE: canvas_noise / webgl_noise are NOT supported by requests-based
        # HTTP clients (XhsClient). They are placeholders for future Playwright
        # migration. Do not rely on them for current风控对抗.
    }
