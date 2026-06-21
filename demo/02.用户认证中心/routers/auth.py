"""认证路由：注册 / 登录 / 刷新令牌 / 登出 / 当前用户。

登录接口使用 OAuth2PasswordRequestForm（表单），以便 Swagger 文档的
"Authorize" 按钮可直接调用并保存 access_token。
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.orm import Session

import config
import crud.role
import crud.token
import crud.user
import schemas
from database import get_db
from deps import get_current_user
from models import User
from security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post(
    "/register",
    response_model=schemas.UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
)
def register(user_in: schemas.UserRegister, db: Session = Depends(get_db)):
    if crud.user.get_user_by_username(db, user_in.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    if crud.user.get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=400, detail="邮箱已被注册")

    user = crud.user.create_user(db, user_in)

    # 注册后默认分配普通用户角色
    default_role = crud.role.get_role_by_name(db, config.DEFAULT_ROLE_NAME)
    if default_role:
        user.roles.append(default_role)
        db.commit()
        db.refresh(user)
    return user


@router.post(
    "/login",
    response_model=schemas.TokenPair,
    summary="用户登录",
)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """登录并返回 access_token + refresh_token。

    `username` 字段既可填用户名也可填邮箱。
    """
    user = crud.user.get_user_by_login(db, form.username)
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="用户已被禁用")

    roles = sorted(crud.user.collect_role_names(user))
    permissions = sorted(crud.user.collect_permissions(user))

    access = create_access_token(str(user.id), user.username, roles, permissions)
    refresh, jti, expires_at = create_refresh_token(str(user.id))
    crud.token.create_refresh_token(db, user.id, jti, refresh, expires_at)

    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": config.ACCESS_TOKEN_EXPIRE_SECONDS,
    }


@router.post(
    "/refresh",
    response_model=schemas.TokenPair,
    summary="刷新令牌",
)
def refresh_token(body: schemas.RefreshRequest, db: Session = Depends(get_db)):
    """使用 refresh_token 换取新的令牌对。

    采用**令牌轮转**策略：旧的 refresh_token 会被吊销，并签发新的令牌对。
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="刷新令牌无效或已过期",
    )
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise credentials_exc
        jti = payload.get("jti")
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        raise credentials_exc

    record = crud.token.get_by_jti(db, jti)
    if not record or record.revoked or record.user_id != user_id:
        raise credentials_exc
    if record.expires_at < datetime.utcnow():
        raise credentials_exc

    # 吊销旧令牌，实现轮转
    crud.token.revoke(db, record)

    user = crud.user.get_user(db, user_id)
    if not user or not user.is_active:
        raise credentials_exc

    roles = sorted(crud.user.collect_role_names(user))
    permissions = sorted(crud.user.collect_permissions(user))
    access = create_access_token(str(user.id), user.username, roles, permissions)
    new_refresh, new_jti, new_expires = create_refresh_token(str(user.id))
    crud.token.create_refresh_token(db, user.id, new_jti, new_refresh, new_expires)

    return {
        "access_token": access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
        "expires_in": config.ACCESS_TOKEN_EXPIRE_SECONDS,
    }


@router.post(
    "/logout",
    response_model=schemas.Message,
    summary="登出",
)
def logout(body: schemas.RefreshRequest, db: Session = Depends(get_db)):
    """登出并吊销当前 refresh_token。"""
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="令牌类型错误")
        jti = payload.get("jti")
    except JWTError:
        raise HTTPException(status_code=400, detail="刷新令牌无效")

    record = crud.token.get_by_jti(db, jti)
    if record and not record.revoked:
        crud.token.revoke(db, record)
    return {"message": "已登出"}


@router.get(
    "/me",
    response_model=schemas.UserRead,
    summary="获取当前登录用户",
)
def me(user: User = Depends(get_current_user)):
    return user
