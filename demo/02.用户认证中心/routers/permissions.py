"""权限管理路由（需 permission:manage 权限）。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import crud.permission
import schemas
from database import get_db
from deps import require_permissions
from models import User

router = APIRouter(prefix="/permissions", tags=["角色与权限"])


@router.get(
    "/",
    response_model=list[schemas.PermissionRead],
    summary="权限列表",
)
def list_permissions(
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("permission:manage")),
):
    return crud.permission.get_permissions(db)


@router.post(
    "/",
    response_model=schemas.PermissionRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建权限",
)
def create_permission(
    perm_in: schemas.PermissionCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("permission:manage")),
):
    if crud.permission.get_permission_by_code(db, perm_in.code):
        raise HTTPException(status_code=400, detail="权限编码已存在")
    return crud.permission.create_permission(db, perm_in)
