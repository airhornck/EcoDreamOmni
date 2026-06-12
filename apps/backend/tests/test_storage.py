"""Tests for src.core.storage — P0-1 v4.0 alignment.

Validates:
  - LocalStorage save / delete / get_url / save_bytes
  - OSSStorage instantiation (mocked, no real credentials)
  - Storage factory behavior (OSS configured → OSSStorage, else LocalStorage)
  - Singleton reset
"""

import io
from unittest.mock import MagicMock, patch

import pytest
from fastapi import UploadFile

from src.core.storage import (
    LocalStorage,
    OSSStorage,
    get_storage,
    reset_storage,
)


# ─── Helpers ───

def _make_upload_file(filename: str, content: bytes, content_type: str = "application/octet-stream") -> UploadFile:
    return UploadFile(
        filename=filename,
        file=io.BytesIO(content),
        size=len(content),
        headers={"content-type": content_type},
    )


@pytest.fixture(autouse=True)
def _reset_storage_singleton():
    """Auto-reset storage singleton before each test."""
    reset_storage()
    yield
    reset_storage()


# ─── LocalStorage ───

@pytest.mark.asyncio
async def test_local_storage_save(tmp_path):
    storage = LocalStorage(str(tmp_path))
    content = b"hello world"
    file = _make_upload_file("hello.txt", content, "text/plain")

    result = await storage.save(file, subdir="docs")

    assert result["original_name"] == "hello.txt"
    assert result["size"] == len(content)
    assert result["file_type"] == "document"
    assert result["file_url"].startswith("/uploads/docs/")
    # Verify file exists on disk
    disk_path = tmp_path / result["file_path"].replace("/uploads/", "")
    assert disk_path.exists()
    assert disk_path.read_bytes() == content


@pytest.mark.asyncio
async def test_local_storage_save_without_subdir(tmp_path):
    storage = LocalStorage(str(tmp_path))
    content = b"no subdir"
    file = _make_upload_file("plain.txt", content)

    result = await storage.save(file)

    assert result["file_url"].startswith("/uploads/")
    assert "/docs/" not in result["file_url"]


@pytest.mark.asyncio
async def test_local_storage_save_rejects_oversized(tmp_path):
    storage = LocalStorage(str(tmp_path))
    content = b"x" * (51 * 1024 * 1024)  # 51MB
    file = _make_upload_file("big.pdf", content, "application/pdf")

    with pytest.raises(ValueError, match="File too large"):
        await storage.save(file, max_size=50 * 1024 * 1024)


def test_local_storage_delete(tmp_path):
    storage = LocalStorage(str(tmp_path))
    target = tmp_path / "202601" / "test.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("delete me")

    file_url = "/uploads/202601/test.txt"
    assert storage.delete(file_url) is True
    assert not target.exists()


def test_local_storage_delete_missing(tmp_path):
    storage = LocalStorage(str(tmp_path))
    assert storage.delete("/uploads/nonexistent.txt") is False


def test_local_storage_get_url(tmp_path):
    storage = LocalStorage(str(tmp_path))
    assert storage.get_url("/uploads/test.jpg") == "/uploads/test.jpg"


def test_local_storage_save_bytes(tmp_path):
    storage = LocalStorage(str(tmp_path))
    content = b"raw bytes content"

    result = storage.save_bytes(content, "raw.bin", subdir="bytes")

    assert result["size"] == len(content)
    assert result["file_url"].startswith("/uploads/bytes/")
    disk_path = tmp_path / result["file_path"].replace("/uploads/", "")
    assert disk_path.read_bytes() == content


# ─── OSSStorage (Mocked) ───

def test_oss_storage_init_missing_package():
    """Should raise RuntimeError when oss2 is not installed."""
    with patch.dict("sys.modules", {"oss2": None}):
        with pytest.raises(RuntimeError, match="oss2 package is required"):
            OSSStorage(
                access_key_id="key",
                access_key_secret="secret",
                bucket_name="bucket",
                endpoint="oss-cn-hangzhou.aliyuncs.com",
            )


def test_oss_storage_get_url_with_cdn():
    """get_url should return CDN-prefixed URL when cdn_domain is set."""
    mock_oss2 = MagicMock()
    mock_auth = MagicMock()
    mock_bucket = MagicMock()
    mock_oss2.Auth.return_value = mock_auth
    mock_oss2.Bucket.return_value = mock_bucket

    with patch.dict("sys.modules", {"oss2": mock_oss2}):
        storage = OSSStorage(
            access_key_id="key",
            access_key_secret="secret",
            bucket_name="mybucket",
            endpoint="oss-cn-hangzhou.aliyuncs.com",
            cdn_domain="cdn.example.com",
        )
        assert storage.get_url("uploads/test.jpg") == "https://cdn.example.com/uploads/test.jpg"
        assert storage.get_url("https://cdn.example.com/existing.jpg") == "https://cdn.example.com/existing.jpg"


# ─── Factory ───

def test_get_storage_returns_local_when_oss_unconfigured():
    """When no OSS env vars, factory should return LocalStorage."""
    with patch("src.core.storage.settings") as mock_settings:
        mock_settings.OSS_ACCESS_KEY_ID = ""
        mock_settings.OSS_ACCESS_KEY_SECRET = ""
        mock_settings.OSS_BUCKET = ""
        mock_settings.OSS_ENDPOINT = ""
        mock_settings.UPLOAD_DIR = "test_uploads"

        storage = get_storage()
        assert isinstance(storage, LocalStorage)


def test_get_storage_returns_oss_when_configured():
    """When OSS env vars are set, factory should return OSSStorage."""
    mock_oss2 = MagicMock()
    mock_auth = MagicMock()
    mock_bucket = MagicMock()
    mock_oss2.Auth.return_value = mock_auth
    mock_oss2.Bucket.return_value = mock_bucket

    with patch.dict("sys.modules", {"oss2": mock_oss2}):
        with patch("src.core.storage.settings") as mock_settings:
            mock_settings.OSS_ACCESS_KEY_ID = "key_id"
            mock_settings.OSS_ACCESS_KEY_SECRET = "secret"
            mock_settings.OSS_BUCKET = "bucket"
            mock_settings.OSS_ENDPOINT = "oss-cn-hangzhou.aliyuncs.com"
            mock_settings.OSS_CDN_DOMAIN = None

            storage = get_storage()
            assert isinstance(storage, OSSStorage)


def test_get_storage_singleton():
    """Multiple calls should return the same instance (singleton)."""
    with patch("src.core.storage.settings") as mock_settings:
        mock_settings.OSS_ACCESS_KEY_ID = ""
        mock_settings.OSS_ACCESS_KEY_SECRET = ""
        mock_settings.OSS_BUCKET = ""
        mock_settings.OSS_ENDPOINT = ""
        mock_settings.UPLOAD_DIR = "singleton_test"

        s1 = get_storage()
        s2 = get_storage()
        assert s1 is s2


def test_reset_storage():
    """reset_storage should clear singleton, next get_storage creates new instance."""
    with patch("src.core.storage.settings") as mock_settings:
        mock_settings.OSS_ACCESS_KEY_ID = ""
        mock_settings.OSS_ACCESS_KEY_SECRET = ""
        mock_settings.OSS_BUCKET = ""
        mock_settings.OSS_ENDPOINT = ""
        mock_settings.UPLOAD_DIR = "reset_test"

        s1 = get_storage()
        reset_storage()
        s2 = get_storage()
        assert s1 is not s2
