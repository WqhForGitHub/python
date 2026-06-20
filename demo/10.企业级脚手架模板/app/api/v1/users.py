"""用户管理路由（需权限）。"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_permissions
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import Message
from app.schemas.user import AssignRoles, UserRead, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get(
    "/",
    response_model=list[UserRead],
    summary="用户列表",
    dependencies=[Depends(require_permissions("user:read"))],
)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    return await user_service.list_users(db, skip, limit)


@router.get(
    "/me",
    response_model=UserRead,
    summary="当前用户信息（仅需登录）",
)
async def get_me(user: User = Depends(get_current_user)):
    return user


@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="用户详情",
    dependencies=[Depends(require_permissions("user:read"))],
)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    return await user_service.get_user(db, user_id)


@router.put(
    "/{user_id}",
    response_model=UserRead,
    summary="更新用户",
    dependencies=[Depends(require_permissions("user:write"))],
)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await user_service.update_user(db, user_id, data)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除用户",
    dependencies=[Depends(require_permissions("user:delete"))],
)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    await user_service.delete_user(db, user_id)
    return None


@router.put(
    "/{user_id}/roles",
    response_model=UserRead,
    summary="分配角色",
    dependencies=[Depends(require_permissions("user:assign_role"))],
)
async def assign_roles(
    user_id: int,
    data: AssignRoles,
    db: AsyncSession = Depends(get_db),
):
    return await user_service.assign_roles(db, user_id, data)
