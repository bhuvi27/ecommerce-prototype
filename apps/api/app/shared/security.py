import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import get_settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: uuid.UUID, role: str) -> str:
    s = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=s.jwt_access_expire_minutes)
    return jwt.encode(
        {"sub": str(user_id), "role": role, "type": "access", "exp": expire},
        s.jwt_access_secret,
        algorithm=ALGORITHM,
    )


def create_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def decode_access_token(token: str) -> dict[str, Any]:
    s = get_settings()
    try:
        payload = jwt.decode(token, s.jwt_access_secret, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise JWTError("invalid token type")
        return payload
    except JWTError as e:
        raise ValueError("Invalid token") from e
