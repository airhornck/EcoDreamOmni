"""
XHS publisher tests: per-account config resolution, fallback, error handling.
"""

import pytest
from unittest.mock import MagicMock, patch

from src.models.account_pool import (
    FingerprintProfile,
    ProxyConfig,
    clear_pool_entries,
    create_pool_entry,
)
from src.models.proxy_config import clear_proxy_entries
from src.services.proxy_service import create_proxy
from src.services.xhs_publisher import check_account_status, publish_to_xhs


@pytest.fixture(autouse=True)
def clean_dbs():
    clear_pool_entries()
    clear_proxy_entries()
    yield
    clear_pool_entries()
    clear_proxy_entries()


def _make_account_with_proxy():
    proxy = create_proxy(
        name="TestProxy", provider="custom", protocol="http",
        host="proxy.test", port=3128, username="u", password="p", region="US"
    )
    account = create_pool_entry(
        platform="xhs",
        account_id="acc_001",
        nickname="Tester",
        cookie="a1=per_account_cookie;webId=123",
        persona="cat",
        content_vertical="health",
        lifecycle_phase="growth",
        fingerprint_profile=FingerprintProfile(
            user_agent="CustomUA/1.0",
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
            timezone="Asia/Shanghai",
            canvas_noise=True,
            webgl_noise=True,
        ),
        proxy_config=ProxyConfig(proxy_id=proxy.id, type="http", region="US"),
    )
    return account, proxy


def test_publish_to_xhs_uses_per_account_config(client):
    account, proxy = _make_account_with_proxy()

    with patch("src.services.xhs_publisher._get_xhs_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.create_image_note.return_value = {"note_id": "note_123"}
        mock_get_client.return_value = mock_client

        result = publish_to_xhs(
            account_id=account.id,
            content={"title": "Test", "body": "Body", "tags": ["tag1"]},
        )

        assert result["success"] is True
        assert result["platform_post_id"] == "note_123"

        call = mock_get_client.call_args
        assert "per_account_cookie" in call.kwargs["cookie"]
        assert call.kwargs["user_agent"] == "CustomUA/1.0"
        proxy_url = call.kwargs["proxies"].get("http", "")
        assert "proxy.test:3128" in proxy_url
        assert "u:p@" in proxy_url


def test_publish_to_xhs_fallback_global_cookie(client):
    with patch("src.services.xhs_publisher.settings") as mock_settings:
        mock_settings.REDNOTE_COOKIE = "a1=fallback_cookie"

        with patch("src.services.xhs_publisher._get_xhs_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.create_image_note.return_value = {"note_id": "fb_123"}
            mock_get_client.return_value = mock_client

            result = publish_to_xhs(
                account_id="nonexistent_account",
                content={"title": "Test", "body": "Body"},
            )

            assert result["success"] is True
            call = mock_get_client.call_args
            assert "fallback_cookie" in call.kwargs["cookie"]
            assert call.kwargs["proxies"] is None


def test_publish_to_xhs_missing_cookie():
    with patch("src.services.xhs_publisher.settings") as mock_settings:
        mock_settings.REDNOTE_COOKIE = ""
        result = publish_to_xhs(
            account_id="nonexistent_account",
            content={"title": "Test", "body": "Body"},
        )
        assert result["success"] is False
        assert "cookie" in result["error"].lower() or "not configured" in result["error"].lower()


def test_publish_to_xhs_no_proxy_when_inactive(client):
    account, proxy = _make_account_with_proxy()
    from src.services.proxy_service import update_proxy
    update_proxy(proxy.id, is_active=False)

    with patch("src.services.xhs_publisher._get_xhs_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.create_image_note.return_value = {"note_id": "note_123"}
        mock_get_client.return_value = mock_client

        result = publish_to_xhs(account_id=account.id, content={"title": "T", "body": "B"})
        assert result["success"] is True
        call = mock_get_client.call_args
        assert call.kwargs["proxies"] is None


def test_publish_to_xhs_records_proxy_result(client):
    account, proxy = _make_account_with_proxy()

    with patch("src.services.xhs_publisher._get_xhs_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.create_image_note.return_value = {"note_id": "note_123"}
        mock_get_client.return_value = mock_client

        publish_to_xhs(account_id=account.id, content={"title": "T", "body": "B"})

        from src.services.proxy_service import get_proxy
        p = get_proxy(proxy.id)
        assert p.success_count >= 1
        assert p.health_status == "healthy"


def test_publish_to_xhs_empty_content():
    account, _ = _make_account_with_proxy()
    result = publish_to_xhs(account_id=account.id, content={"title": "", "body": ""})
    assert result["success"] is False
    assert "required" in result["error"].lower()


def test_check_account_status_healthy(client):
    account, _ = _make_account_with_proxy()

    with patch("src.services.xhs_publisher._get_xhs_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.get_self_info2.return_value = {
            "user_id": "123",
            "nickname": "Tester",
        }
        mock_client.create_image_note.return_value = {}
        mock_get_client.return_value = mock_client

        status = check_account_status(account.cookie)
        assert status["healthy"] is True
        assert status["user_id"] == "123"
        assert status["nickname"] == "Tester"


def test_check_account_status_unhealthy(client):
    account, _ = _make_account_with_proxy()

    with patch("src.services.xhs_publisher._get_xhs_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.get_self_info2.return_value = {
            "user_id": "123",
            "nickname": "Tester",
        }
        mock_client.create_image_note.side_effect = Exception("Banned")
        mock_get_client.return_value = mock_client

        status = check_account_status(account.cookie)
        assert status["healthy"] is False
        assert status["reason"]
