"""安全工具：密码哈希 + JWT 编解码。

- 密码哈希使用 passlib + bcrypt
- JWT 使用 python-jose
- access_token  短期有效，携带用户角色与权限，用于接口鉴权
- refresh_token 长期有效，仅携带用户 ID 与 jti，用于换取新的令牌对
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any

from jose import jwt
from passlib.context import CryptContext

import config

# CryptContext：自动识别哈希格式，便于将来更换算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============================================================
# 密码
# ============================================================
def hash_password(password: str) -> str:
    """对明文密码做哈希。"""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """校验明文密码与哈希是否匹配。"""
    return pwd_context.verify(plain, hashed)


# ============================================================
# JWT
# ============================================================
def _create_token(
    data: dict[str, Any],
    expires_delta: timedelta,
    token_type: str,
) -> tuple[str, str, datetime]:
    """构造 JWT。

    返回 (token, jti, expires_at)。
    """
    iat = datetime.utcnow()
    expire = iat + expires_delta
    jti = secrets.token_hex(16)  # 唯一标识，refresh token 入库用于吊销
    to_encode = {
        **data,
        "iat": iat,
        "exp": expire,
        "type": token_type,
        "jti": jti,
    }
    token = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return token, jti, expire


def create_access_token(
    sub: str,
    username: str,
    roles: list[str],
    permissions: list[str],
) -> str:
    """签发 access_token。

    携带角色与权限，便于网关 / 接口层快速鉴权，无需每次查库。
    """
    token, _, _ = _create_token(
        {"sub": sub, "username": username, "roles": roles, "permissions": permissions},
        timedelta(seconds=config.ACCESS_TOKEN_EXPIRE_SECONDS),
        "access",
    )
    return token


def create_refresh_token(sub: str) -> tuple[str, str, datetime]:
    """签发 refresh_token。

    返回 (token, jti, expires_at)。jti 与 expires_at 用于入库管理。
    """
    return _create_token(
        {"sub": sub},
        timedelta(seconds=config.REFRESH_TOKEN_EXPIRE_SECONDS),
        "refresh",
    )


def decode_token(token: str) -> dict[str, Any]:
    """解码并校验 JWT（包含 exp 过期校验）。失败抛出 JWTError。"""
    return jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])


def hash_token(token: str) -> str:
    """对 refresh_token 做哈希后存储，避免明文落库。"""
    return hashlib.sha256(token.encode()).hexdigest()
