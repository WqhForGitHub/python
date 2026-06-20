"""JWT 编解码工具。"""
from datetime import datetime, timedelta

from jose import jwt

import config


def create_access_token(user_id: int, username: str) -> str:
    iat = datetime.utcnow()
    expire = iat + timedelta(seconds=config.ACCESS_TOKEN_EXPIRE_SECONDS)
    payload = {
        "sub": str(user_id),
        "username": username,
        "iat": iat,
        "exp": expire,
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
