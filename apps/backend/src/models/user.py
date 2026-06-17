"""User model and database operations (MVP with PostgreSQL).

NOTE: CRUD functions have been moved to src.services.auth_function.py
per FUNC-ARCH red-line. The re-exports below are for backward compatibility
and will be removed in a future cleanup.
"""

from typing import Optional



class User:
    """Lightweight dataclass wrapper for UserORM results."""

    def __init__(
        self,
        id: str,
        email: str,
        username: str,
        hashed_password: str,
        role: str = "operator",
        is_active: bool = True,
        mfa_secret: Optional[str] = None,
        mfa_enabled: bool = False,
        tenant_id: Optional[str] = None,
    ):
        self.id = id
        self.email = email
        self.username = username
        self.hashed_password = hashed_password
        self.role = role
        self.is_active = is_active
        self.mfa_secret = mfa_secret
        self.mfa_enabled = mfa_enabled
        self.tenant_id = tenant_id


def clear_users() -> None:
    """No-op for DB-backed users — for testing compatibility only."""
