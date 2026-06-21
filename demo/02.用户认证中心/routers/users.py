"""用户管理路由（需相应权限）。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import crud.role
import crud.user
import schemas
from database import get_db
from deps import require_permissions
from models import User

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get(
    "/",
    response_model=list[schemas.UserRead],
    summary="用户列表",
)
def list_users(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("user:read")),
):
    return crud.user.get_users(db, skip=skip, limit=limit)


@router.get(
    "/{user_id}",
    response_model=schemas.UserRead,
    summary="用户详情",
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("user:read")),
):
    user = crud.user.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"用户 ID {user_id} 不存在")
    return user


@router.put(
    "/{user_id}",
    response_model=schemas.UserRead,
    summary="更新用户",
)
def update_user(
    user_id: int,
    user_in: schemas.UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("user:write")),
):
    user = crud.user.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"用户 ID {user_id} 不存在")

    if user_in.email and user_in.email != user.email:
        if crud.user.get_user_by_email(db, user_in.email):
            raise HTTPException(status_code=400, detail="邮箱已被注册")
    return crud.user.update_user(db, user, user_in)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除用户",
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("user:delete")),
):
    user = crud.user.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"用户 ID {user_id} 不存在")
    crud.user.delete_user(db, user)
    return None


@router.put(
    "/{user_id}/roles",
    response_model=schemas.UserRead,
    summary="分配角色（全量覆盖）",
)
def assign_roles(
    user_id: int,
    body: schemas.AssignRoles,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("user:assign_role")),
):
    user = crud.user.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"用户 ID {user_id} 不存在")

    roles = crud.role.get_roles_by_ids(db, body.role_ids)
    if len(roles) != len(set(body.role_ids)):
        raise HTTPException(status_code=400, detail="部分角色 ID 不存在")
    return crud.user.set_roles(db, user, body.role_ids)
