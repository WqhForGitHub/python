"""认证路由：注册 / 登录 / 刷新 / 当前用户。"""
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import UserRegister
from app.schemas.common import Message, RefreshRequest, TokenPair
from app.schemas.user import UserRead
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserRead, summary="注册")
async def register(user_in: UserRegister, db: AsyncSession = Depends(get_db)):
    return await auth_service.register(db, user_in)


@router.post("/login", response_model=TokenPair, summary="登录")
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await auth_service.authenticate(db, form.username, form.password)
    return await auth_service.issue_tokens(user)


@router.post("/refresh", response_model=TokenPair, summary="刷新令牌")
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.refresh_tokens(db, body.refresh_token)


@router.get("/me", response_model=UserRead, summary="当前登录用户")
async def me(user: User = Depends(get_current_user)):
    return user


@router.post("/logout", response_model=Message, summary="登出")
async def logout():
    # Demo 简化：refresh token 未入库，登出仅提示前端丢弃令牌
    return Message(message="已登出，请清除本地令牌")
