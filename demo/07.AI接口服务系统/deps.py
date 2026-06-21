"""FastAPI 依赖项：当前用户 + 限流。

Demo 简化：通过 `X-User-Id` 请求头标识用户。
"""

from fastapi import Depends, Header, HTTPException, Request, status

import limiter


def get_user_id(x_user_id: int | None = Header(None, alias="X-User-Id")) -> int:
    if x_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请在请求头携带 X-User-Id",
        )
    return x_user_id


def rate_limit(user_id: int = Depends(get_user_id)) -> int:
    """令牌桶限流：每用户独立桶，不足则 429。"""
    if not limiter.limiter.allow(str(user_id)):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求过于频繁，请稍后再试",
            headers={"Retry-After": "1"},
        )
    return user_id
