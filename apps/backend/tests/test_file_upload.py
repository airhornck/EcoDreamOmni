"""Tests for src.core.file_upload — P0-1 v4.0 alignment.

Validates:
  - File type detection (mime + extension)
  - Filename sanitization
  - Per-type size limits (image ≤10MB, document ≤50MB, video ≤100MB)
  - Allowed extension enforcement
  - Integration with storage backend (local)
"""

import io
from pathlib import Path

import pytest
from fastapi import UploadFile

from src.core import file_upload as fu
from src.core.storage import LocalStorage, reset_storage


# ─── Helpers ───

def _make_upload_file(filename: str, content: bytes, content_type: str = "application/octet-stream") -> UploadFile:
    """Create a minimal UploadFile for testing."""
    return UploadFile(
        filename=filename,
        file=io.BytesIO(content),
        size=len(content),
        headers={"content-type": content_type},
    )


@pytest.fixture
def temp_storage(tmp_path):
    """Provide a LocalStorage instance using pytest tmp_path."""
    storage = LocalStorage(str(tmp_path))
    yield storage
    reset_storage()


# ─── File Type Detection ───

@pytest.mark.parametrize(
    "mime_type,filename,expected",
    [
        ("image/jpeg", "photo.jpg", "image"),
        ("image/png", "icon.png", "image"),
        ("image/webp", "img.webp", "image"),
        ("video/mp4", "clip.mp4", "video"),
        ("application/pdf", "doc.pdf", "document"),
        ("text/csv", "data.csv", "spreadsheet"),
        ("application/vnd.ms-excel", "sheet.xls", "spreadsheet"),
        (None, "archive.zip", "unknown"),
        ("application/octet-stream", "file.unknown", "unknown"),
    ],
)
def test_get_file_type(mime_type, filename, expected):
    assert fu.get_file_type(mime_type, filename) == expected


# ─── Filename Sanitization ───

@pytest.mark.parametrize(
    "raw,expected",
    [
        ("normal.jpg", "normal.jpg"),
        ("../../etc/passwd", "passwd"),
        ("path/to/file.pdf", "file.pdf"),
        ("file with spaces.png", "file with spaces.png"),
        ("", "unnamed"),
    ],
)
def test_safe_filename(raw, expected):
    assert fu._safe_filename(raw) == expected


# ─── Per-Type Size Limits ───

def test_file_type_size_limits():
    assert fu.get_max_size_for_file_type("image") == 10 * 1024 * 1024
    assert fu.get_max_size_for_file_type("document") == 50 * 1024 * 1024
    assert fu.get_max_size_for_file_type("video") == 100 * 1024 * 1024
    assert fu.get_max_size_for_file_type("audio") == 50 * 1024 * 1024
    assert fu.get_max_size_for_file_type("spreadsheet") == 10 * 1024 * 1024
    assert fu.get_max_size_for_file_type("unknown") == 50 * 1024 * 1024


# ─── Upload Save (Local Storage) ───

@pytest.mark.asyncio
async def test_save_upload_file_image_success(temp_storage, tmp_path):
    """Image under 10MB should save successfully."""
    content = b"\xff\xd8\xff\xe0fake jpeg header" + b"x" * 1000
    file = _make_upload_file("test.jpg", content, "image/jpeg")

    reset_storage()
    # Monkey-patch get_storage to return our temp storage
    from src.core import storage as st
    st._storage_instance = temp_storage

    result = await fu.save_upload_file(file, subdir="test_imgs")

    assert result["original_name"] == "test.jpg"
    assert result["file_type"] == "image"
    assert result["size"] == len(content)
    assert result["file_url"].startswith("/uploads/test_imgs/")
    assert Path(tmp_path / result["file_path"].replace("/uploads/", "")).exists()

    reset_storage()


@pytest.mark.asyncio
async def test_save_upload_file_image_over_limit(temp_storage):
    """Image over 10MB should raise ValueError."""
    content = b"\xff\xd8\xff\xe0" + b"x" * (11 * 1024 * 1024)  # ~11MB
    file = _make_upload_file("huge.jpg", content, "image/jpeg")

    reset_storage()
    from src.core import storage as st
    st._storage_instance = temp_storage

    with pytest.raises(ValueError, match="File too large"):
        await fu.save_upload_file(file)

    reset_storage()


@pytest.mark.asyncio
async def test_save_upload_file_video_under_limit(temp_storage, tmp_path):
    """Video under 100MB should save successfully."""
    content = b"\x00\x00\x00\x20ftyp" + b"x" * (50 * 1024 * 1024)  # ~50MB
    file = _make_upload_file("demo.mp4", content, "video/mp4")

    reset_storage()
    from src.core import storage as st
    st._storage_instance = temp_storage

    result = await fu.save_upload_file(file)

    assert result["file_type"] == "video"
    assert result["size"] == len(content)

    reset_storage()


@pytest.mark.asyncio
async def test_save_upload_file_document_over_limit(temp_storage):
    """Document over 50MB should raise ValueError."""
    content = b"%PDF-1.4" + b"x" * (51 * 1024 * 1024)  # ~51MB
    file = _make_upload_file("huge.pdf", content, "application/pdf")

    reset_storage()
    from src.core import storage as st
    st._storage_instance = temp_storage

    with pytest.raises(ValueError, match="File too large"):
        await fu.save_upload_file(file)

    reset_storage()


@pytest.mark.asyncio
async def test_save_upload_file_explicit_max_size(temp_storage, tmp_path):
    """Explicit max_size should override per-type default."""
    content = b"\xff\xd8\xff\xe0" + b"x" * (15 * 1024 * 1024)  # ~15MB image
    file = _make_upload_file("big.jpg", content, "image/jpeg")

    reset_storage()
    from src.core import storage as st
    st._storage_instance = temp_storage

    # With explicit max_size=20MB (override image 10MB limit)
    result = await fu.save_upload_file(file, max_size=20 * 1024 * 1024)
    assert result["size"] == len(content)

    reset_storage()


@pytest.mark.asyncio
async def test_save_upload_file_disallowed_extension(temp_storage):
    """Extension not in ALLOWED_EXTENSIONS should raise ValueError."""
    content = b"<?xml version='1.0'?><root/>"
    file = _make_upload_file("malicious.xml", content, "application/xml")

    reset_storage()
    from src.core import storage as st
    st._storage_instance = temp_storage

    with pytest.raises(ValueError, match="File type not allowed"):
        await fu.save_upload_file(file)

    reset_storage()


# ─── Delete ───

def test_delete_upload_file_local(temp_storage, tmp_path):
    """Delete should remove the file from local storage."""
    reset_storage()
    from src.core import storage as st
    st._storage_instance = temp_storage

    # Create a file inside the temp_storage upload_dir
    target = tmp_path / "202601" / "test_del.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("delete me")
    file_url = "/uploads/202601/test_del.txt"

    assert target.exists()
    assert fu.delete_upload_file(file_url) is True
    assert not target.exists()

    reset_storage()


def test_delete_upload_file_missing(temp_storage):
    """Delete non-existent file should return False."""
    assert fu.delete_upload_file("/uploads/nonexistent.txt") is False
