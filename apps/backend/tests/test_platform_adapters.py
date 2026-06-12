"""Tests for Platform Adapters (W20).

Red-Green TDD for:
  - XHS format/validate
  - Douyin format/validate
  - WeChat Channels format/validate
  - Spec retrieval
  - Unsupported platform handling
"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.services import platform_adapters as pa


# ─── Specs ───

def test_list_platforms():
    platforms = pa.list_supported_platforms()
    assert "xhs" in platforms
    assert "douyin" in platforms
    assert "wechat_channels" in platforms


def test_get_adapter_xhs():
    adapter = pa.get_adapter("xhs")
    assert adapter.platform == "xhs"
    assert adapter.spec.max_title_length == 20


def test_get_adapter_unsupported():
    with pytest.raises(ValueError, match="Unsupported platform"):
        pa.get_adapter("twitter")


def test_compare_specs():
    specs = pa.compare_platform_specs()
    assert "xhs" in specs
    assert specs["xhs"]["max_title_length"] == 20
    assert specs["douyin"]["max_video_duration_sec"] == 180


# ─── XHS formatting ───

def test_xhs_format_basic():
    adapter = pa.get_adapter("xhs")
    payload = adapter.format_content(
        title="Dog nutrition tips for beginners",
        body="Here are some tips...",
        tags=["dog", "nutrition"],
        images=["img1.jpg", "img2.jpg"],
    )
    assert payload["platform"] == "xhs"
    assert payload["title"] == "Dog nutrition tips for beginners"  # title preserved
    assert "#dog" in payload["body"]
    assert "#nutrition" in payload["body"]
    assert payload["images"] == ["img1.jpg", "img2.jpg"]  # images preserved


def test_xhs_validate_pass():
    adapter = pa.get_adapter("xhs")
    payload = adapter.format_content(
        title="Short title",
        body="Body text",
        tags=["tag1"],
    )
    result = adapter.validate_payload(payload)
    assert result["valid"] is True
    assert result["errors"] == []


def test_xhs_validate_title_too_long():
    adapter = pa.get_adapter("xhs")
    payload = adapter.format_content(
        title="A" * 25,
        body="Body",
    )
    result = adapter.validate_payload(payload)
    assert result["valid"] is False
    assert any("Title too long" in e for e in result["errors"])


# ─── Douyin formatting ───

def test_douyin_format_basic():
    adapter = pa.get_adapter("douyin")
    payload = adapter.format_content(
        title="Amazing dog video!",
        body="Watch this cute dog playing...",
        tags=["dog", "cute"],
        video="video.mp4",
    )
    assert payload["platform"] == "douyin"
    assert payload["music_required"] is True
    assert "caption" in payload
    assert "#dog" in payload["caption"]
    assert payload["video"] == "video.mp4"


def test_douyin_validate_missing_video():
    adapter = pa.get_adapter("douyin")
    payload = adapter.format_content(
        title="Title",
        body="Body",
    )
    result = adapter.validate_payload(payload)
    assert result["valid"] is False
    assert any("Missing required field: video" in e for e in result["errors"])


# ─── WeChat Channels formatting ───

def test_wechat_format_basic():
    adapter = pa.get_adapter("wechat_channels")
    payload = adapter.format_content(
        title="WeChat video",
        body="Content here",
        tags=["pet"],
        images=["cover.jpg"],
        video="video.mp4",
    )
    assert payload["platform"] == "wechat_channels"
    assert payload["cover_image"] == "cover.jpg"
    assert "#pet" in payload["body"]


def test_wechat_auto_cover():
    adapter = pa.get_adapter("wechat_channels")
    payload = adapter.format_content(
        title="Auto cover test",
        body="Body",
        images=["img1.jpg"],
    )
    assert payload["cover_image"] == "img1.jpg"


def test_wechat_validate_missing_cover():
    adapter = pa.get_adapter("wechat_channels")
    payload = adapter.format_content(
        title="Title",
        body="Body",
    )
    result = adapter.validate_payload(payload)
    assert result["valid"] is False
    assert any("Missing required field: cover_image" in e for e in result["errors"])


# ─── Cross-platform comparison ───

def test_title_length_differs():
    xhs = pa.get_adapter("xhs")
    douyin = pa.get_adapter("douyin")
    wechat = pa.get_adapter("wechat_channels")

    title = "This is a very long title that exceeds most platform limits"
    xhs_payload = xhs.format_content(title=title, body="Body")
    douyin_payload = douyin.format_content(title=title, body="Body")
    wechat_payload = wechat.format_content(title=title, body="Body")

    # format_content preserves title; validation catches overflow
    assert xhs.validate_payload(xhs_payload)["valid"] is False
    assert douyin.validate_payload(douyin_payload)["valid"] is False
    assert wechat.validate_payload(wechat_payload)["valid"] is False


def test_image_limits():
    xhs = pa.get_adapter("xhs")
    wechat = pa.get_adapter("wechat_channels")

    images = [f"img{i}.jpg" for i in range(25)]
    xhs_payload = xhs.format_content(title="T", body="B", images=images)
    wechat_payload = wechat.format_content(title="T", body="B", images=images)

    # format_content preserves all images; validation warns about overflow
    xhs_val = xhs.validate_payload(xhs_payload)
    wechat_val = wechat.validate_payload(wechat_payload)
    assert any("Too many images" in w for w in xhs_val["warnings"])
    assert any("Too many images" in w for w in wechat_val["warnings"])
