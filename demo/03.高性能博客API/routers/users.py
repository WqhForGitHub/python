"""用户路由。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

import crud.user
import schemas
from database import get_db

router = APIRouter(prefix="/users", tags=["用户"])


@router.post(
    "/",
    response_model=schemas.UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建用户",
)
async def create_user(user_in: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    return await crud.user.create_user(db, user_in)


@router.get(
    "/",
    response_model=list[schemas.UserRead],
    summary="用户列表",
)
async def list_users(db: AsyncSession = Depends(get_db)):
    return await crud.user.get_users(db)


@router.get(
    "/{user_id}",
    response_model=schemas.UserRead,
    summary="用户详情",
)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await crud.user.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"用户 ID {user_id} 不存在")
    return user
