"""Auth service: registration, login, token management.

DB operations delegated to auth_function.py per FUNC-ARCH red-line.
"""

from datetime import timedelta
from typing import Any, Optional, Tuple

from src.core.security import create_access_token, get_password_hash, verify_password
from src.models.user import User
from src.services import auth_function as af


async def register_user(
    db: Any,
    email: str,
    password: str,
    username: str,
    role: str = "operator",
) -> Tuple[User, str, str]:
    hashed = get_password_hash(password)
    user = await af.create_user(
        db, email=email, username=username, hashed_password=hashed, role=role
    )
    access_token = create_access_token({"sub": user.id, "role": user.role})
    refresh_token = create_access_token(
        {"sub": user.id, "type": "refresh"}, expires_delta=timedelta(days=7)
    )
    return user, access_token, refresh_token


async def authenticate_user(
    db: Any, email: str, password: str
) -> Optional[Tuple[User, str, str]]:
    user = await af.get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    access_token = create_access_token({"sub": user.id, "role": user.role})
    refresh_token = create_access_token(
        {"sub": user.id, "type": "refresh"}, expires_delta=timedelta(days=7)
    )
    return user, access_token, refresh_token


async def setup_mfa(db: Any, user_id: str) -> str:
    """Generate and store MFA secret. Returns the secret for QR code generation."""
    import secrets

    secret = secrets.token_hex(20)
    await af.update_user_mfa(db, user_id, secret, enabled=False)
    return secret


async def verify_mfa_code(db: Any, user_id: str, code: str) -> bool:
    """Verify TOTP code. MVP: simple 6-digit check (replace with pyotp in production)."""
    user = await af.get_user_by_id(db, user_id)
    if not user or not user.mfa_secret:
        return False
    # MVP: accept any 6-digit code for testing structure
    # Production: use pyotp.TOTP(user.mfa_secret).verify(code)
    return len(code) == 6 and code.isdigit()
