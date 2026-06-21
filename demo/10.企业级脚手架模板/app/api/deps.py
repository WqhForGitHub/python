"""API 层依赖：当前用户 / RBAC 权限校验。"""

from typing import Callable

from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AuthError, PermissionDeniedError
from app.core.security import decode_token
from app.models.user import User
from app.repositories.user import UserRepository
from app.services.user_service import collect_permissions

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not token:
        raise AuthError("缺少访问令牌")
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise AuthError("令牌类型错误")
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        raise AuthError("令牌无效或已过期")

    repo = UserRepository(db)
    user = await repo.get_with_roles(user_id)
    if user is None:
        raise AuthError("用户不存在")
    if not user.is_active:
        raise PermissionDeniedError("用户已被禁用")
    return user


def require_permissions(*required: str) -> Callable[..., User]:
    """RBAC 权限校验依赖工厂（满足其一即可）。"""
    required_set = set(required)

    async def checker(user: User = Depends(get_current_user)) -> User:
        if user.is_superuser:
            return user
        user_perms = collect_permissions(user)
        if not (required_set & user_perms):
            raise PermissionDeniedError(
                f"权限不足，需要以下权限之一：{', '.join(required)}"
            )
        return user

    return checker


def require_roles(*required: str) -> Callable[..., User]:
    """角色校验依赖工厂（满足其一即可）。"""
    required_set = set(required)

    async def checker(user: User = Depends(get_current_user)) -> User:
        if user.is_superuser:
            return user
        user_roles = {r.name for r in user.roles}
        if not (required_set & user_roles):
            raise PermissionDeniedError(
                f"角色不足，需要以下角色之一：{', '.join(required)}"
            )
        return user

    return checker
