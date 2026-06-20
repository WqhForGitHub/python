"""安全工具：密码哈希 + JWT 编解码。"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _create_token(data: dict[str, Any], expires_delta: timedelta, token_type: str) -> tuple[str, str]:
    iat = datetime.utcnow()
    expire = iat + expires_delta
    jti = secrets.token_hex(16)
    to_encode = {**data, "iat": iat, "exp": expire, "type": token_type, "jti": jti}
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM), jti


def create_access_token(sub: str, username: str, roles: list[str]) -> str:
    token, _ = _create_token(
        {"sub": sub, "username": username, "roles": roles},
        timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS),
        "access",
    )
    return token


def create_refresh_token(sub: str) -> tuple[str, str]:
    return _create_token(
        {"sub": sub},
        timedelta(seconds=settings.REFRESH_TOKEN_EXPIRE_SECONDS),
        "refresh",
    )


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
