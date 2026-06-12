"""Auth API routes: register, login, me, MFA."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.dependencies import get_current_user
from src.models.user import User
from src.services.auth_service import (
    authenticate_user,
    register_user,
    setup_mfa,
    verify_mfa_code,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    username: str
    role: str = "operator"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class MFASetupResponse(BaseModel):
    secret: str


class MFAEnableRequest(BaseModel):
    code: str


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=TokenResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    try:
        user, access_token, refresh_token = await register_user(
            db=db,
            email=req.email,
            password=req.password,
            username=req.username,
            role=req.role,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={"id": user.id, "email": user.email, "username": user.username, "role": user.role},
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await authenticate_user(db, req.email, req.password)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    user, access_token, refresh_token = result
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={"id": user.id, "email": user.email, "username": user.username, "role": user.role},
    )


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "username": user.username, "role": user.role}


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def mfa_setup(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    secret = await setup_mfa(db, user.id)
    return MFASetupResponse(secret=secret)


@router.post("/mfa/enable")
async def mfa_enable(
    req: MFAEnableRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not await verify_mfa_code(db, user.id, req.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code"
        )
    from src.models.user import update_user_mfa

    await update_user_mfa(db, user.id, user.mfa_secret or "", enabled=True)
    return {"message": "MFA enabled"}
