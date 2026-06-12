"""Storage abstraction layer — local filesystem or Aliyun OSS.

Supports seamless switching between local dev and production via environment variables.
If OSS credentials are not configured, falls back to local filesystem (backward compatible).
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Protocol
from urllib.parse import urljoin

from fastapi import UploadFile

from src.core.config import settings


class StorageBackend(Protocol):
    """Protocol for storage backends."""

    async def save(
        self,
        file: UploadFile,
        subdir: str = "",
        allowed_extensions: Optional[set] = None,
        max_size: int = 50 * 1024 * 1024,
    ) -> dict:
        ...

    def delete(self, file_url: str) -> bool:
        ...

    def get_url(self, file_url: str) -> str:
        ...


class LocalStorage:
    """Local filesystem storage — development fallback."""

    def __init__(self, upload_dir: str):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save(
        self,
        file: UploadFile,
        subdir: str = "",
        allowed_extensions: Optional[set] = None,
        max_size: int = 50 * 1024 * 1024,
    ) -> dict:
        from src.core.file_upload import (
            ALLOWED_EXTENSIONS,
            _generate_file_hash,
            _safe_filename,
            get_file_type,
        )

        content = await file.read()
        size = len(content)
        if size > max_size:
            raise ValueError(f"File too large: {size} bytes (max {max_size})")

        original_name = _safe_filename(file.filename or "unnamed")
        ext = Path(original_name).suffix.lower()
        allowed = allowed_extensions or ALLOWED_EXTENSIONS
        if ext not in allowed:
            raise ValueError(f"File type not allowed: {ext}")

        date_dir = datetime.now().strftime("%Y%m")
        file_hash = _generate_file_hash(content)
        stored_name = f"{file_hash}_{original_name}"

        target_dir = self.upload_dir / subdir / date_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / stored_name

        with open(file_path, "wb") as f:
            f.write(content)

        file_url = (
            f"/uploads/{subdir}/{date_dir}/{stored_name}"
            if subdir
            else f"/uploads/{date_dir}/{stored_name}"
        )

        return {
            "filename": stored_name,
            "original_name": original_name,
            "file_path": str(file_path),
            "file_url": file_url,
            "mime_type": file.content_type or "application/octet-stream",
            "size": size,
            "file_type": get_file_type(file.content_type, original_name),
        }

    def delete(self, file_url: str) -> bool:
        if file_url.startswith("/uploads/"):
            rel_path = file_url[len("/uploads/"):]
            path = self.upload_dir / rel_path
        else:
            path = Path(file_url)
        if path.exists():
            path.unlink()
            return True
        return False

    def get_url(self, file_url: str) -> str:
        return file_url

    def save_bytes(
        self,
        content: bytes,
        filename: str,
        subdir: str = "",
    ) -> dict:
        """Save raw bytes to local storage."""
        date_dir = datetime.now().strftime("%Y%m")
        file_hash = hashlib.sha256(content).hexdigest()[:16]
        stored_name = f"{file_hash}_{filename}"

        target_dir = self.upload_dir / subdir / date_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / stored_name

        with open(file_path, "wb") as f:
            f.write(content)

        file_url = (
            f"/uploads/{subdir}/{date_dir}/{stored_name}"
            if subdir
            else f"/uploads/{date_dir}/{stored_name}"
        )

        return {
            "filename": stored_name,
            "file_path": str(file_path),
            "file_url": file_url,
            "size": len(content),
        }


class OSSStorage:
    """Aliyun OSS storage — production backend."""

    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        bucket_name: str,
        endpoint: str,
        cdn_domain: Optional[str] = None,
    ):
        try:
            import oss2
        except ImportError:
            raise RuntimeError(
                "oss2 package is required for OSS storage. "
                "Install with: pip install oss2"
            )

        self.auth = oss2.Auth(access_key_id, access_key_secret)
        self.bucket = oss2.Bucket(self.auth, endpoint, bucket_name)
        self.bucket_name = bucket_name
        self.endpoint = endpoint
        self.cdn_domain = cdn_domain or endpoint

    async def save(
        self,
        file: UploadFile,
        subdir: str = "",
        allowed_extensions: Optional[set] = None,
        max_size: int = 50 * 1024 * 1024,
    ) -> dict:
        from src.core.file_upload import (
            ALLOWED_EXTENSIONS,
            _safe_filename,
            get_file_type,
        )

        content = await file.read()
        size = len(content)
        if size > max_size:
            raise ValueError(f"File too large: {size} bytes (max {max_size})")

        original_name = _safe_filename(file.filename or "unnamed")
        ext = Path(original_name).suffix.lower()
        allowed = allowed_extensions or ALLOWED_EXTENSIONS
        if ext not in allowed:
            raise ValueError(f"File type not allowed: {ext}")

        date_dir = datetime.now().strftime("%Y%m")
        file_hash = hashlib.sha256(content).hexdigest()[:16]
        stored_name = f"{file_hash}_{original_name}"

        oss_key = f"uploads/{subdir}/{date_dir}/{stored_name}" if subdir else f"uploads/{date_dir}/{stored_name}"

        # Upload to OSS
        self.bucket.put_object(oss_key, content)

        # Public URL (or CDN URL)
        if self.cdn_domain and not self.cdn_domain.startswith("http"):
            public_url = f"https://{self.cdn_domain}/{oss_key}"
        elif self.cdn_domain:
            public_url = urljoin(self.cdn_domain + "/", oss_key)
        else:
            public_url = f"https://{self.bucket_name}.{self.endpoint}/{oss_key}"

        return {
            "filename": stored_name,
            "original_name": original_name,
            "file_path": oss_key,  # OSS object key
            "file_url": public_url,
            "mime_type": file.content_type or "application/octet-stream",
            "size": size,
            "file_type": get_file_type(file.content_type, original_name),
        }

    def delete(self, file_url: str) -> bool:
        """Delete from OSS. file_url can be full URL or object key."""
        # Extract object key from URL
        if file_url.startswith("http"):
            # Try to extract key from URL
            if self.bucket_name in file_url and self.endpoint in file_url:
                prefix = f"https://{self.bucket_name}.{self.endpoint}/"
                key = file_url[len(prefix):]
            elif self.cdn_domain and self.cdn_domain in file_url:
                protocol = "https://" if "https://" in file_url else "http://"
                prefix = f"{protocol}{self.cdn_domain}/"
                key = file_url[len(prefix):]
            else:
                key = file_url.split("/")[-1]
                key = f"uploads/{datetime.now().strftime('%Y%m')}/{key}"
        else:
            key = file_url

        try:
            self.bucket.delete_object(key)
            return True
        except Exception:
            return False

    def get_url(self, file_url: str) -> str:
        """Return public URL. If already a full URL, return as-is."""
        if file_url.startswith("http"):
            return file_url
        # file_url is an OSS key, generate public URL
        if self.cdn_domain and not self.cdn_domain.startswith("http"):
            return f"https://{self.cdn_domain}/{file_url}"
        elif self.cdn_domain:
            return urljoin(self.cdn_domain + "/", file_url)
        return f"https://{self.bucket_name}.{self.endpoint}/{file_url}"

    def save_bytes(
        self,
        content: bytes,
        filename: str,
        subdir: str = "",
    ) -> dict:
        """Save raw bytes to OSS."""
        date_dir = datetime.now().strftime("%Y%m")
        file_hash = hashlib.sha256(content).hexdigest()[:16]
        stored_name = f"{file_hash}_{filename}"

        oss_key = f"uploads/{subdir}/{date_dir}/{stored_name}" if subdir else f"uploads/{date_dir}/{stored_name}"

        self.bucket.put_object(oss_key, content)

        if self.cdn_domain and not self.cdn_domain.startswith("http"):
            public_url = f"https://{self.cdn_domain}/{oss_key}"
        elif self.cdn_domain:
            public_url = urljoin(self.cdn_domain + "/", oss_key)
        else:
            public_url = f"https://{self.bucket_name}.{self.endpoint}/{oss_key}"

        return {
            "filename": stored_name,
            "file_path": oss_key,
            "file_url": public_url,
            "size": len(content),
        }


# ─── Singleton factory ───

_storage_instance: Optional[StorageBackend] = None


def get_storage() -> StorageBackend:
    """Get the configured storage backend (lazy singleton)."""
    global _storage_instance
    if _storage_instance is not None:
        return _storage_instance

    # Check if OSS is configured
    oss_key_id = getattr(settings, "OSS_ACCESS_KEY_ID", "")
    oss_key_secret = getattr(settings, "OSS_ACCESS_KEY_SECRET", "")
    oss_bucket = getattr(settings, "OSS_BUCKET", "")
    oss_endpoint = getattr(settings, "OSS_ENDPOINT", "")

    if oss_key_id and oss_key_secret and oss_bucket and oss_endpoint:
        _storage_instance = OSSStorage(
            access_key_id=oss_key_id,
            access_key_secret=oss_key_secret,
            bucket_name=oss_bucket,
            endpoint=oss_endpoint,
            cdn_domain=getattr(settings, "OSS_CDN_DOMAIN", None),
        )
    else:
        upload_dir = getattr(settings, "UPLOAD_DIR", "uploads")
        _storage_instance = LocalStorage(upload_dir)

    return _storage_instance


def reset_storage() -> None:
    """Reset storage singleton (mainly for testing)."""
    global _storage_instance
    _storage_instance = None
