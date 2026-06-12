"""File upload utilities — unified storage interface.

Delegates to src.core.storage which auto-selects Local or OSS backend.
"""

import hashlib
from pathlib import Path
from typing import Optional

from fastapi import UploadFile

from src.core.config import settings

UPLOAD_DIR = settings.UPLOAD_DIR

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB — fallback default

# Per-file-type size limits (v4.0 P0-1 alignment)
FILE_TYPE_SIZE_LIMITS = {
    "image": 10 * 1024 * 1024,       # 10MB
    "document": 50 * 1024 * 1024,    # 50MB
    "video": 100 * 1024 * 1024,      # 100MB
    "audio": 50 * 1024 * 1024,       # 50MB
    "spreadsheet": 10 * 1024 * 1024, # 10MB
    "unknown": 50 * 1024 * 1024,     # 50MB
}

ALLOWED_EXTENSIONS = {
    # Documents
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".txt", ".md",
    # Images
    ".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".svg",
    # Videos
    ".mp4", ".mov", ".avi", ".mkv", ".webm",
}

def _generate_file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()[:16]


def _safe_filename(original: str) -> str:
    """Sanitize original filename, keep extension."""
    name = Path(original).name
    # Remove path traversal chars
    name = name.replace("..", "").replace("/", "").replace("\\", "")
    if not name:
        name = "unnamed"
    return name


def get_file_type(mime_type: Optional[str], filename: str) -> str:
    """Derive high-level file type from mime or extension."""
    if mime_type:
        if mime_type.startswith("image/"):
            return "image"
        if mime_type.startswith("video/"):
            return "video"
        if mime_type.startswith("audio/"):
            return "audio"
        if mime_type in (
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ):
            return "document"
        if mime_type in (
            "text/csv",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ):
            return "spreadsheet"
    ext = Path(filename).suffix.lower()
    if ext in (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".svg"):
        return "image"
    if ext in (".mp4", ".mov", ".avi", ".mkv", ".webm"):
        return "video"
    if ext in (".pdf", ".doc", ".docx", ".txt", ".md"):
        return "document"
    if ext in (".csv", ".xls", ".xlsx"):
        return "spreadsheet"
    return "unknown"


def get_max_size_for_file_type(file_type: str) -> int:
    """Return max file size in bytes for a given file type."""
    return FILE_TYPE_SIZE_LIMITS.get(file_type, MAX_FILE_SIZE)


async def save_upload_file(
    file: UploadFile,
    subdir: str = "",
    allowed_extensions: Optional[set] = None,
    max_size: Optional[int] = None,
) -> dict:
    """Save an UploadFile to configured storage (local or OSS).

    If max_size is not provided, uses per-file-type limits:
      image ≤ 10MB, document ≤ 50MB, video ≤ 100MB, etc.

    Returns:
        {
            "filename": str,
            "original_name": str,
            "file_path": str,         # local path or OSS object key
            "file_url": str,          # URL for serving
            "mime_type": str,
            "size": int,
            "file_type": str,
        }
    """
    from src.core.storage import get_storage

    # Determine effective max_size: explicit > per-type > global fallback
    effective_max = max_size
    if effective_max is None:
        # Peek at filename to infer type for limit selection
        original_name = _safe_filename(file.filename or "unnamed")
        inferred_type = get_file_type(file.content_type, original_name)
        effective_max = get_max_size_for_file_type(inferred_type)

    storage = get_storage()
    return await storage.save(
        file,
        subdir=subdir,
        allowed_extensions=allowed_extensions,
        max_size=effective_max,
    )


def delete_upload_file(file_url: str) -> bool:
    """Delete a file from configured storage."""
    from src.core.storage import get_storage

    storage = get_storage()
    return storage.delete(file_url)
