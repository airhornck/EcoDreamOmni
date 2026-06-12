"""Platform Adapters — W20: multi-platform content format adaptation.

Platforms:
  - xhs (小红书): title + body + images/video, hashtags inline, max title 20 chars
  - douyin (抖音): short video primary, title ≤ 55 chars, hashtags, music required
  - wechat_channels (视频号): video/image, title ≤ 30 chars, cover image required

Each adapter provides:
  - format_content(): transform generic draft → platform-specific payload
  - validate_payload(): check platform constraints
  - get_specs(): return platform format specifications
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class PlatformSpec:
    name: str
    max_title_length: int
    max_body_length: int
    max_images: int
    max_video_duration_sec: int
    supports_carousel: bool
    hashtag_style: str  # inline | separate
    required_fields: List[str]


_PLATFORM_SPECS: Dict[str, PlatformSpec] = {
    "xhs": PlatformSpec(
        name="xiaohongshu",
        max_title_length=20,
        max_body_length=1000,
        max_images=18,
        max_video_duration_sec=600,
        supports_carousel=True,
        hashtag_style="inline",
        required_fields=["title", "body"],
    ),
    "douyin": PlatformSpec(
        name="douyin",
        max_title_length=55,
        max_body_length=500,
        max_images=0,  # Video primary
        max_video_duration_sec=180,
        supports_carousel=False,
        hashtag_style="inline",
        required_fields=["title", "video"],
    ),
    "wechat_channels": PlatformSpec(
        name="wechat_channels",
        max_title_length=30,
        max_body_length=800,
        max_images=9,
        max_video_duration_sec=300,
        supports_carousel=False,
        hashtag_style="inline",
        required_fields=["title", "cover_image"],
    ),
}


class PlatformAdapter:
    """Base adapter for platform-specific content formatting."""

    def __init__(self, platform: str):
        self.platform = platform.lower()
        self.spec = _PLATFORM_SPECS.get(self.platform)
        if self.spec is None:
            raise ValueError(f"Unsupported platform: {platform}")

    def format_content(
        self,
        title: str,
        body: str,
        tags: Optional[List[str]] = None,
        images: Optional[List[str]] = None,
        video: Optional[str] = None,
        cover_image: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Transform generic content into platform-specific payload."""
        tags = tags or []
        images = images or []

        if self.platform == "xhs":
            return self._format_xhs(title, body, tags, images, video)
        elif self.platform == "douyin":
            return self._format_douyin(title, body, tags, video)
        elif self.platform == "wechat_channels":
            return self._format_wechat_channels(title, body, tags, images, video, cover_image)
        else:
            raise ValueError(f"No formatter for platform: {self.platform}")

    def _format_xhs(
        self,
        title: str,
        body: str,
        tags: List[str],
        images: List[str],
        video: Optional[str],
    ) -> Dict[str, Any]:
        # Append hashtags inline (no truncation — validation will catch overflows)
        hashtag_line = " ".join(f"#{t}" for t in tags)
        formatted_body = body
        if hashtag_line:
            formatted_body += f"\n\n{hashtag_line}"

        return {
            "platform": "xhs",
            "title": title,
            "body": formatted_body,
            "images": images,
            "video": video,
            "hashtags": tags,
            "format_version": "v1",
        }

    def _format_douyin(
        self,
        title: str,
        body: str,
        tags: List[str],
        video: Optional[str],
    ) -> Dict[str, Any]:
        # Douyin: short punchy title, body is caption
        caption = body
        hashtag_line = " ".join(f"#{t}" for t in tags)
        if hashtag_line:
            caption += f" {hashtag_line}"

        return {
            "platform": "douyin",
            "title": title,
            "caption": caption,
            "video": video,
            "hashtags": tags,
            "music_required": True,
            "format_version": "v1",
        }

    def _format_wechat_channels(
        self,
        title: str,
        body: str,
        tags: List[str],
        images: List[str],
        video: Optional[str],
        cover_image: Optional[str],
    ) -> Dict[str, Any]:
        formatted_body = body
        hashtag_line = " ".join(f"#{t}" for t in tags)
        if hashtag_line:
            formatted_body += f"\n{hashtag_line}"

        # Auto-select cover from first image if not provided
        selected_cover = cover_image or (images[0] if images else None)

        return {
            "platform": "wechat_channels",
            "title": title,
            "body": formatted_body,
            "images": images,
            "video": video,
            "cover_image": selected_cover,
            "hashtags": tags,
            "format_version": "v1",
        }

    def validate_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a platform payload against spec constraints."""
        errors = []
        warnings = []

        # Required fields
        for field in self.spec.required_fields:
            if field == "video" and not payload.get("video"):
                errors.append(f"Missing required field: {field}")
            elif field == "cover_image" and not payload.get("cover_image"):
                errors.append(f"Missing required field: {field}")
            elif field == "title" and not payload.get("title"):
                errors.append(f"Missing required field: {field}")
            elif field == "body" and not payload.get("body"):
                errors.append(f"Missing required field: {field}")

        # Title length
        title = payload.get("title", "")
        if len(title) > self.spec.max_title_length:
            errors.append(
                f"Title too long: {len(title)} > {self.spec.max_title_length}"
            )

        # Body length
        body = payload.get("body", payload.get("caption", ""))
        if len(body) > self.spec.max_body_length:
            errors.append(
                f"Body too long: {len(body)} > {self.spec.max_body_length}"
            )

        # Image count
        images = payload.get("images", [])
        if len(images) > self.spec.max_images:
            warnings.append(
                f"Too many images: {len(images)} > {self.spec.max_images}, will truncate"
            )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def get_specs(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "max_title_length": self.spec.max_title_length,
            "max_body_length": self.spec.max_body_length,
            "max_images": self.spec.max_images,
            "max_video_duration_sec": self.spec.max_video_duration_sec,
            "supports_carousel": self.spec.supports_carousel,
            "hashtag_style": self.spec.hashtag_style,
            "required_fields": self.spec.required_fields,
        }


def get_adapter(platform: str) -> PlatformAdapter:
    return PlatformAdapter(platform)


def list_supported_platforms() -> List[str]:
    return list(_PLATFORM_SPECS.keys())


def compare_platform_specs() -> Dict[str, Dict[str, Any]]:
    """Return comparison of all platform specs."""
    return {name: spec.__dict__ for name, spec in _PLATFORM_SPECS.items()}
