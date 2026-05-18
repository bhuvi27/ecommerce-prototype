import uuid
from typing import Annotated
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.db.models import User, UserRole
from app.shared.db.session import get_db
from app.shared.security import decode_access_token

bearer = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    db: Annotated[AsyncSession, Depends(get_db)],
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> User | None:
    if not creds:
        return None
    try:
        payload = decode_access_token(creds.credentials)
        user_id = uuid.UUID(payload["sub"])
    except (ValueError, KeyError):
        return None
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_current_user(
    user: Annotated[User | None, Depends(get_current_user_optional)],
) -> User:
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


async def get_admin_user(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user


def get_guest_id(request: Request) -> str | None:
    return request.headers.get("X-Cart-Id") or request.cookies.get("cart_id")
