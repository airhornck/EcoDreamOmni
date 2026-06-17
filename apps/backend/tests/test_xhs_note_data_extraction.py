"""Tests for xhs_note_data_extraction Skill and engagement fetch logic.

Red-Green TDD — W13 DataAnalyst 24h data recovery.
"""


from src.services.xhs_note_data_extraction import (
    _extract_user_id,
    _parse_interact_info,
    _to_int,
    fetch_note_engagement,
)


# ───────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────


def test_extract_user_id_standard():
    """Extract user_id from typical get_self_info2 response."""
    self_info = {"data": {"user_id": "abc123"}}
    assert _extract_user_id(self_info) == "abc123"


def test_extract_user_id_nested():
    """Extract user_id from nested user object."""
    self_info = {"data": {"user": {"user_id": "nested456"}}}
    assert _extract_user_id(self_info) == "nested456"


def test_extract_user_id_missing():
    """Return None when user_id is missing."""
    assert _extract_user_id({}) is None
    assert _extract_user_id({"data": {}}) is None


def test_parse_interact_info_full():
    """Parse complete interact_info dict."""
    interact = {
        "liked_count": 100,
        "comment_count": 20,
        "collected_count": 30,
        "share_count": 5,
        "view_count": 1000,
    }
    result = _parse_interact_info(interact)
    assert result["likes"] == 100
    assert result["comments"] == 20
    assert result["saves"] == 30
    assert result["shares"] == 5
    assert result["views"] == 1000


def test_parse_interact_info_partial():
    """Handle missing fields gracefully."""
    interact = {"liked_count": 50}
    result = _parse_interact_info(interact)
    assert result["likes"] == 50
    assert result["comments"] is None
    assert result["saves"] is None


def test_to_int_valid():
    assert _to_int(42) == 42
    assert _to_int("99") == 99


def test_to_int_invalid():
    assert _to_int(None) is None
    assert _to_int("abc") is None
    assert _to_int({}) is None


# ───────────────────────────────────────────────
# fetch_note_engagement — parameter validation
# ───────────────────────────────────────────────


def test_fetch_missing_account_id():
    result = fetch_note_engagement({"platform_post_id": "note123"})
    assert result["success"] is False
    assert "account_id" in result["error"].lower()


def test_fetch_missing_note_id():
    result = fetch_note_engagement({"account_id": "acc001"})
    assert result["success"] is False
    assert "platform_post_id" in result["error"].lower()


def test_fetch_account_not_found():
    result = fetch_note_engagement({
        "account_id": "nonexistent_account",
        "platform_post_id": "note123",
    })
    assert result["success"] is False
    assert "not found" in result["error"].lower()


# ───────────────────────────────────────────────
# fetch_note_engagement — toggle check
# ───────────────────────────────────────────────


def test_fetch_disabled_by_default(monkeypatch):
    """Auto engagement fetch must be disabled by default (PRD V2.3)."""
    from src.models.account_pool import create_pool_entry, clear_pool_entries

    clear_pool_entries()
    fp = {
        "user_agent": "ua",
        "viewport": {"width": 1920, "height": 1080},
        "locale": "zh-CN",
        "timezone": "Asia/Shanghai",
    }
    entry = create_pool_entry(
        platform="xhs",
        account_id="test_acc",
        nickname="Test",
        cookie="cookie",
        persona="p",
        content_vertical="cv",
        lifecycle_phase="growth",
        fingerprint_profile=fp,
    )

    # Default: auto_engagement_fetch = False
    result = fetch_note_engagement({
        "account_id": entry.id,
        "platform_post_id": "note123",
    })
    assert result["success"] is False
    assert "disabled" in result["error"].lower()

    clear_pool_entries()


def test_fetch_enabled_account(monkeypatch):
    """When enabled, proceed to fetch (will fail on client init since no real cookie)."""
    from src.models.account_pool import create_pool_entry, clear_pool_entries, update_pool_entry

    clear_pool_entries()
    fp = {
        "user_agent": "ua",
        "viewport": {"width": 1920, "height": 1080},
        "locale": "zh-CN",
        "timezone": "Asia/Shanghai",
    }
    entry = create_pool_entry(
        platform="xhs",
        account_id="test_acc",
        nickname="Test",
        cookie="",
        persona="p",
        content_vertical="cv",
        lifecycle_phase="growth",
        fingerprint_profile=fp,
    )
    update_pool_entry(entry.id, auto_engagement_fetch=True)

    # Empty cookie will cause client init to fail — this is expected behavior
    result = fetch_note_engagement({
        "account_id": entry.id,
        "platform_post_id": "note123",
    })
    assert result["success"] is False
    assert "client" in result["error"].lower() or "cookie" in result["error"].lower()

    clear_pool_entries()


# ───────────────────────────────────────────────
# fetch_note_engagement — mock success path
# ───────────────────────────────────────────────


def test_fetch_success_with_mock_client(monkeypatch):
    """Happy path: mock XHS client returns note with interact_info."""
    from src.models.account_pool import create_pool_entry, clear_pool_entries, update_pool_entry

    clear_pool_entries()
    fp = {
        "user_agent": "ua",
        "viewport": {"width": 1920, "height": 1080},
        "locale": "zh-CN",
        "timezone": "Asia/Shanghai",
    }
    entry = create_pool_entry(
        platform="xhs",
        account_id="test_acc",
        nickname="Test",
        cookie="a1=xxx; webId=yyy",
        persona="p",
        content_vertical="cv",
        lifecycle_phase="growth",
        fingerprint_profile=fp,
    )
    update_pool_entry(entry.id, auto_engagement_fetch=True)

    # Mock _get_xhs_client and its methods
    class MockClient:
        def get_self_info2(self):
            return {"data": {"user_id": "user123"}}

        def get_user_notes(self, user_id):
            return {
                "notes": [
                    {
                        "note_id": "note456",
                        "interact_info": {
                            "liked_count": 150,
                            "comment_count": 25,
                            "collected_count": 40,
                            "share_count": 8,
                        },
                    }
                ]
            }

    def mock_get_client(*args, **kwargs):
        return MockClient()

    monkeypatch.setattr(
        "src.services.xhs_publisher._get_xhs_client",
        mock_get_client,
    )

    result = fetch_note_engagement({
        "account_id": entry.id,
        "platform_post_id": "note456",
    })

    assert result["success"] is True
    metrics = result["metrics"]
    assert metrics["likes"] == 150
    assert metrics["comments"] == 25
    assert metrics["saves"] == 40
    assert metrics["shares"] == 8

    clear_pool_entries()


def test_fetch_note_not_in_list(monkeypatch):
    """When note is not in recent notes list, should try strategy 2 then fail."""
    from src.models.account_pool import create_pool_entry, clear_pool_entries, update_pool_entry

    clear_pool_entries()
    fp = {
        "user_agent": "ua",
        "viewport": {"width": 1920, "height": 1080},
        "locale": "zh-CN",
        "timezone": "Asia/Shanghai",
    }
    entry = create_pool_entry(
        platform="xhs",
        account_id="test_acc",
        nickname="Test",
        cookie="a1=xxx",
        persona="p",
        content_vertical="cv",
        lifecycle_phase="growth",
        fingerprint_profile=fp,
    )
    update_pool_entry(entry.id, auto_engagement_fetch=True)

    class MockClient:
        def get_self_info2(self):
            return {"data": {"user_id": "user123"}}

        def get_user_notes(self, user_id):
            return {"notes": []}  # Note not found

        def get_notes_statistics(self, **kwargs):
            return {"data": {"items": []}}  # Also not found

    monkeypatch.setattr(
        "src.services.xhs_publisher._get_xhs_client",
        lambda *a, **k: MockClient(),
    )

    result = fetch_note_engagement({
        "account_id": entry.id,
        "platform_post_id": "note999",
    })

    assert result["success"] is False
    assert "exhausted" in result["error"].lower() or "not found" in result["error"].lower()

    clear_pool_entries()
