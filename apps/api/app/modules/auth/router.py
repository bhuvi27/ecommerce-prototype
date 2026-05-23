import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.shared.db.models import Address, RefreshToken, User, UserRole
from app.shared.db.session import get_db
from app.shared.deps import get_current_user
from app.shared.security import (
    create_access_token, create_refresh_token, hash_password, hash_token,
    verify_password,
)
from app.modules.auth.schemas import (
    AddressCreate, AddressResponse, LoginRequest, ProfileUpdate,
    RegisterRequest, TokenResponse, UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])
REFRESH_COOKIE = "refresh_token"


def _user_response(u: User) -> UserResponse:
    return UserResponse(id=u.id, email=u.email, name=u.name, role=u.role.value)


@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest, response: Response, db: Annotated[AsyncSession, Depends(get_db)]):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=body.email, password_hash=hash_password(body.password), name=body.name)
    db.add(user)
    await db.flush()
    access = create_access_token(user.id, user.role.value)
    refresh = await _issue_refresh(db, user.id)
    response.set_cookie(REFRESH_COOKIE, refresh, httponly=True, samesite="lax", max_age=get_settings().jwt_refresh_expire_days * 86400)
    return TokenResponse(access_token=access, user=_user_response(user))


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, response: Response, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise HTTPException(status_code=423, detail="Account locked. Try later.")
    if not verify_password(body.password, user.password_hash):
        user.failed_logins += 1
        if user.failed_logins >= 5:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
        await db.flush()
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user.failed_logins = 0
    user.locked_until = None
    access = create_access_token(user.id, user.role.value)
    refresh = await _issue_refresh(db, user.id)
    response.set_cookie(REFRESH_COOKIE, refresh, httponly=True, samesite="lax", max_age=get_settings().jwt_refresh_expire_days * 86400)
    return TokenResponse(access_token=access, user=_user_response(user))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token_endpoint(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")
    th = hash_token(token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == th, RefreshToken.expires_at > datetime.now(timezone.utc))
    )
    rt = result.scalar_one_or_none()
    if not rt:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user_result = await db.execute(select(User).where(User.id == rt.user_id))
    user = user_result.scalar_one()
    await db.delete(rt)
    access = create_access_token(user.id, user.role.value)
    new_refresh = await _issue_refresh(db, user.id)
    response.set_cookie(REFRESH_COOKIE, new_refresh, httponly=True, samesite="lax", max_age=get_settings().jwt_refresh_expire_days * 86400)
    return TokenResponse(access_token=access, user=_user_response(user))


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(REFRESH_COOKIE)
    return {"ok": True}


@router.get("/me", response_model=UserResponse)
async def me(user: Annotated[User, Depends(get_current_user)]):
    return _user_response(user)


@router.patch("/me", response_model=UserResponse)
async def update_profile(body: ProfileUpdate, user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    if body.name is not None:
        user.name = body.name
    await db.flush()
    return _user_response(user)


@router.get("/addresses", response_model=list[AddressResponse])
async def list_addresses(user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(Address)
        .where(Address.user_id == user.id)
        .order_by(Address.is_default.desc(), Address.created_at.desc())
    )
    return result.scalars().all()


@router.post("/addresses", response_model=AddressResponse, status_code=201)
async def create_address(body: AddressCreate, user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    if body.is_default:
        await db.execute(update(Address).where(Address.user_id == user.id).values(is_default=False))
    addr = Address(user_id=user.id, **body.model_dump())
    db.add(addr)
    await db.flush()
    return addr


async def _issue_refresh(db: AsyncSession, user_id: uuid.UUID) -> str:
    s = get_settings()
    token = create_refresh_token()
    rt = RefreshToken(
        user_id=user_id,
        token_hash=hash_token(token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=s.jwt_refresh_expire_days),
    )
    db.add(rt)
    await db.flush()
    return token
