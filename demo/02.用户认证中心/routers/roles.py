"""角色管理路由（需相应权限）。"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import crud.permission
import crud.role
import schemas
from database import get_db
from deps import require_permissions
from models import User

router = APIRouter(prefix="/roles", tags=["角色与权限"])


@router.get(
    "/",
    response_model=list[schemas.RoleDetail],
    summary="角色列表",
)
def list_roles(
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("role:read")),
):
    return crud.role.get_roles(db)


@router.post(
    "/",
    response_model=schemas.RoleDetail,
    status_code=status.HTTP_201_CREATED,
    summary="创建角色",
)
def create_role(
    role_in: schemas.RoleCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("role:write")),
):
    if crud.role.get_role_by_name(db, role_in.name):
        raise HTTPException(status_code=400, detail="角色名已存在")
    return crud.role.create_role(db, role_in)


@router.get(
    "/{role_id}",
    response_model=schemas.RoleDetail,
    summary="角色详情",
)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("role:read")),
):
    role = crud.role.get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail=f"角色 ID {role_id} 不存在")
    return role


@router.put(
    "/{role_id}",
    response_model=schemas.RoleDetail,
    summary="更新角色",
)
def update_role(
    role_id: int,
    role_in: schemas.RoleUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("role:write")),
):
    role = crud.role.get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail=f"角色 ID {role_id} 不存在")
    return crud.role.update_role(db, role, role_in)


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除角色",
)
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("role:delete")),
):
    role = crud.role.get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail=f"角色 ID {role_id} 不存在")
    crud.role.delete_role(db, role)
    return None


@router.put(
    "/{role_id}/permissions",
    response_model=schemas.RoleDetail,
    summary="为角色分配权限（全量覆盖）",
)
def assign_permissions(
    role_id: int,
    body: schemas.AssignPermissions,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("role:write")),
):
    role = crud.role.get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail=f"角色 ID {role_id} 不存在")

    perms = crud.permission.get_permissions_by_ids(db, body.permission_ids)
    if len(perms) != len(set(body.permission_ids)):
        raise HTTPException(status_code=400, detail="部分权限 ID 不存在")
    return crud.role.set_permissions(db, role, body.permission_ids)
