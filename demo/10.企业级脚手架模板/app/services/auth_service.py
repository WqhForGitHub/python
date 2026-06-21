"""认证业务：注册 / 登录 / 刷新 / 登出。"""

from datetime import datetime

from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthError, ConflictError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.role import Role
from app.models.user import User
from app.repositories.user import RoleRepository, UserRepository
from app.schemas.auth import UserRegister


async def register(db: AsyncSession, user_in: UserRegister) -> User:
    user_repo = UserRepository(db)
    if await user_repo.get_by_username(user_in.username):
        raise ConflictError("用户名已存在")
    if await user_repo.get_by_email(user_in.email):
        raise ConflictError("邮箱已被注册")

    user = User(
        username=user_in.username,
        email=user_in.email,
        password_hash=hash_password(user_in.password),
    )
    # 注册默认分配 user 角色
    role_repo = RoleRepository(db)
    default_role = await role_repo.get_by_name("user")
    if default_role:
        user.roles = [default_role]
    return await user_repo.add(user)


async def authenticate(db: AsyncSession, login: str, password: str) -> User:
    user_repo = UserRepository(db)
    user = await user_repo.get_by_login(login)
    if not user or not verify_password(password, user.password_hash):
        raise AuthError("用户名或密码错误")
    if not user.is_active:
        raise AuthError("用户已被禁用")
    return user


async def collect_role_names(user: User) -> list[str]:
    # roles 已通过 selectinload 加载
    return sorted({r.name for r in user.roles})


async def issue_tokens(user: User) -> dict:
    roles = await collect_role_names(user)
    access = create_access_token(str(user.id), user.username, roles)
    refresh, _jti = create_refresh_token(str(user.id))
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_SECONDS,
    }


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> dict:
    """刷新令牌（轮转）。

    Demo 简化：不持久化 refresh token，仅校验签名与类型。
    生产环境应入库 jti 并支持吊销（见 Demo 02）。
    """
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise AuthError("令牌类型错误")
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        raise AuthError("刷新令牌无效或已过期")

    user_repo = UserRepository(db)
    user = await user_repo.get_with_roles(user_id)
    if not user or not user.is_active:
        raise AuthError("用户不存在或已禁用")

    return await issue_tokens(user)
