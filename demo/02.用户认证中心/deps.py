"""FastAPI 依赖项：数据库 Session、当前用户、RBAC 权限/角色校验。

使用方式：

    # 1. 仅需登录
    @router.get("/profile")
    def profile(user: User = Depends(get_current_user)): ...

    # 2. 需要特定权限（满足其一即可）
    @router.get("/")
    def list_users(_: User = Depends(require_permissions("user:read"))): ...

    # 3. 需要特定角色（满足其一即可）
    @router.get("/")
    def admin_only(_: User = Depends(require_roles("admin"))): ...
"""
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

import crud.user
import models
from database import get_db
from security import decode_token

# tokenUrl 指向登录接口，Swagger 文档的 "Authorize" 按钮会调用它
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """解析 Bearer token 并返回当前用户。"""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exc

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_exc
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        raise credentials_exc

    user = crud.user.get_user(db, user_id)
    if user is None:
        raise credentials_exc
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )
    return user


def require_permissions(*required: str) -> Callable[..., models.User]:
    """权限校验依赖工厂。

    用户需拥有所列权限中的**任意一个**即可访问，否则返回 403。
    """
    required_set = set(required)

    def checker(
        user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> models.User:
        user_perms = crud.user.collect_permissions(user)
        if not (required_set & user_perms):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要以下权限之一：{', '.join(required)}",
            )
        return user

    return checker


def require_roles(*required: str) -> Callable[..., models.User]:
    """角色校验依赖工厂。

    用户需拥有所列角色中的**任意一个**即可访问，否则返回 403。
    """
    required_set = set(required)

    def checker(
        user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> models.User:
        user_roles = crud.user.collect_role_names(user)
        if not (required_set & user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"角色不足，需要以下角色之一：{', '.join(required)}",
            )
        return user

    return checker
