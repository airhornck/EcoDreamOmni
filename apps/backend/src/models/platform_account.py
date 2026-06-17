"""Platform account models, in-memory store, and AES-256-GCM cookie vault."""

import base64
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ─── Cookie Vault (AES-256-GCM) ───

# MVP: derive key from env or fallback; production should use KMS
_VAULT_KEY = os.environ.get("COOKIE_VAULT_KEY", "ecodream-omni-cookie-vault-key-32b!").encode()
_VAULT_KEY_32 = _VAULT_KEY[:32].ljust(32, b"\0")


def _encrypt_cookie(plaintext: str) -> str:
    """Encrypt cookie string with AES-256-GCM. Returns base64(nonce + tag + ciphertext)."""
    nonce = os.urandom(12)
    aesgcm = AESGCM(_VAULT_KEY_32)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    # ciphertext = tag (16 bytes) + encrypted_data
    return base64.b64encode(nonce + ciphertext).decode("ascii")


def _decrypt_cookie(encrypted: str) -> str:
    """Decrypt cookie string."""
    data = base64.b64decode(encrypted.encode("ascii"))
    nonce, ciphertext = data[:12], data[12:]
    aesgcm = AESGCM(_VAULT_KEY_32)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")


# ─── Data Model ───

@dataclass
class PlatformAccount:
    id: str
    platform: str  # xhs, douyin, wechat_channels
    account_id: str
    nickname: str
    cookie_encrypted: str
    status: str  # active, expired, warming, blocked
    created_at: str
    updated_at: str
    last_checked_at: Optional[str] = None
    health_score: float = 100.0

    @property
    def cookie(self) -> str:
        return _decrypt_cookie(self.cookie_encrypted)

    @cookie.setter
    def cookie(self, value: str) -> None:
        self.cookie_encrypted = _encrypt_cookie(value)


# ─── In-Memory Store (MVP phase) ───

_platform_account_db: Dict[str, PlatformAccount] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_platform_account(
    platform: str,
    account_id: str,
    nickname: str,
    cookie: str,
    status: str = "active",
) -> PlatformAccount:
    pa_id = secrets.token_urlsafe(16)
    now = _now()
    pa = PlatformAccount(
        id=pa_id,
        platform=platform,
        account_id=account_id,
        nickname=nickname,
        cookie_encrypted=_encrypt_cookie(cookie),
        status=status,
        created_at=now,
        updated_at=now,
    )
    _platform_account_db[pa_id] = pa
    return pa


def get_platform_account(pa_id: str) -> Optional[PlatformAccount]:
    pa = _platform_account_db.get(pa_id)
    if pa is None:
        return None
    # Return a shallow copy so the caller can read decrypted cookie without mutating storage directly
    return pa


def list_platform_accounts() -> List[PlatformAccount]:
    return list(_platform_account_db.values())


def update_platform_account(pa_id: str, **kwargs) -> Optional[PlatformAccount]:
    pa = _platform_account_db.get(pa_id)
    if pa is None:
        return None
    if "cookie" in kwargs:
        pa.cookie = kwargs.pop("cookie")
    for key, value in kwargs.items():
        if hasattr(pa, key) and key != "cookie":
            setattr(pa, key, value)
    pa.updated_at = _now()
    return pa


def delete_platform_account(pa_id: str) -> bool:
    if pa_id in _platform_account_db:
        del _platform_account_db[pa_id]
        return True
    return False


def clear_platform_accounts() -> None:
    _platform_account_db.clear()


# ─── QR Login Mock State (MVP) ───

_qr_login_state: Dict[str, dict] = {}


def start_qr_login(platform: str) -> dict:
    qr_id = secrets.token_urlsafe(16)
    _qr_login_state[qr_id] = {
        "platform": platform,
        "status": "pending",
        "created_at": _now(),
    }
    return {
        "qr_id": qr_id,
        "qr_url": f"xhsdiscover://login/qrcode?qr_id={qr_id}",
        "platform": platform,
    }


def poll_qr_login(qr_id: str) -> Optional[dict]:
    state = _qr_login_state.get(qr_id)
    if state is None:
        return None
    # MVP: auto-advance to confirmed after first poll for testing
    if state["status"] == "pending":
        state["status"] = "confirmed"
    return {"qr_id": qr_id, "status": state["status"], "platform": state["platform"]}
