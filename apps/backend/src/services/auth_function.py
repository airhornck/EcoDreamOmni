"""Auth Function layer — UserORM CRUD only.

Aligned with FUNC-ARCH: Service层禁止直接数据库访问，所有UserORM操作下沉到Function层。
"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.orm_user import UserORM

if TYPE_CHECKING:
    from src.models.user import User


async def get_user_by_email(db: AsyncSession, email: str) -> Optional["User"]:
    result = await db.execute(select(UserORM).where(UserORM.email == email.lower()))
    orm = result.scalar_one_or_none()
    if not orm:
        return None
    return _to_user(orm)


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional["User"]:
    import uuid

    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        return None
    result = await db.execute(select(UserORM).where(UserORM.id == uid))
    orm = result.scalar_one_or_none()
    if not orm:
        return None
    return _to_user(orm)


async def create_user(
    db: AsyncSession,
    email: str,
    username: str,
    hashed_password: str,
    role: str = "operator",
) -> "User":
    existing = await get_user_by_email(db, email)
    if existing:
        raise ValueError("Email already registered")

    orm = UserORM(
        email=email.lower(),
        username=username,
        hashed_password=hashed_password,
        role=role,
    )
    db.add(orm)
    await db.commit()
    await db.refresh(orm)
    return _to_user(orm)


async def update_user_mfa(
    db: AsyncSession, user_id: str, secret: str, enabled: bool = True
) -> Optional["User"]:
    import uuid

    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        return None

    result = await db.execute(select(UserORM).where(UserORM.id == uid))
    orm = result.scalar_one_or_none()
    if not orm:
        return None

    orm.mfa_secret = secret
    orm.mfa_enabled = enabled
    await db.commit()
    await db.refresh(orm)
    return _to_user(orm)


def _to_user(orm: UserORM) -> "User":
    from src.models.user import User

    return User(
        id=str(orm.id),
        email=orm.email,
        username=orm.username,
        hashed_password=orm.hashed_password,
        role=orm.role,
        is_active=orm.is_active,
        mfa_secret=orm.mfa_secret,
        mfa_enabled=orm.mfa_enabled,
        tenant_id=orm.tenant_id,
    )
