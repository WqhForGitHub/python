"""文件上传 / 下载 / 管理路由。

权限模型：
- public：任何人可下载
- private：仅 owner
- shared：owner + 显式共享的用户
"""
import os

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

import config
import crud.file
import schemas
import storage
from database import get_db
from deps import can_access_file, get_current_user
from models import FileRecord, User

router = APIRouter(prefix="/files", tags=["文件"])


def _validate_filename(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型 {ext}，允许：{sorted(config.ALLOWED_EXTENSIONS)}",
        )
    return filename


@router.post(
    "/upload",
    response_model=schemas.FileRead,
    status_code=status.HTTP_201_CREATED,
    summary="上传文件",
)
async def upload_file(
    file: UploadFile = File(..., description="待上传文件"),
    visibility: str = Query("private", description="public/private/shared"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if visibility not in ("public", "private", "shared"):
        raise HTTPException(status_code=400, detail="visibility 取值非法")

    _validate_filename(file.filename or "")
    data = await file.read()
    if len(data) > config.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"文件过大，最大允许 {config.MAX_UPLOAD_SIZE // 1024 // 1024}MB",
        )
    return crud.file.save_upload(
        db,
        owner_id=user.id,
        filename=file.filename or "unnamed",
        data=data,
        content_type=file.content_type or "",
        visibility=visibility,
    )


@router.get(
    "/",
    response_model=list[schemas.FileRead],
    summary="我的文件列表",
)
def list_my_files(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return crud.file.list_files_by_owner(db, user.id, skip, limit)


@router.get(
    "/public",
    response_model=list[schemas.FileRead],
    summary="公开文件列表",
)
def list_public(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return crud.file.list_public_files(db, skip, limit)


@router.get(
    "/{file_id}",
    response_model=schemas.FileRead,
    summary="文件元信息",
)
def get_file_meta(
    file_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    file = crud.file.get_file(db, file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="文件不存在")
    if not can_access_file(user, file, db):
        raise HTTPException(status_code=403, detail="无权访问该文件")
    return file


@router.get(
    "/{file_id}/download",
    summary="下载文件",
)
def download_file(
    file_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    file = crud.file.get_file(db, file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="文件不存在")
    if not can_access_file(user, file, db):
        raise HTTPException(status_code=403, detail="无权下载该文件")

    data = storage.open(file.stored_key)
    return Response(
        content=data,
        media_type=file.content_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{file.filename}"',
        },
    )


@router.put(
    "/{file_id}",
    response_model=schemas.FileRead,
    summary="更新文件权限（可见性）",
)
def update_file(
    file_id: int,
    body: schemas.FileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    file = crud.file.get_file(db, file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="文件不存在")
    if file.owner_id != user.id:
        raise HTTPException(status_code=403, detail="仅 owner 可修改权限")
    if body.visibility is not None:
        return crud.file.update_visibility(db, file, body.visibility)
    return file


@router.delete(
    "/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除文件（仅 owner）",
)
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    file = crud.file.get_file(db, file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="文件不存在")
    if file.owner_id != user.id:
        raise HTTPException(status_code=403, detail="仅 owner 可删除")
    crud.file.delete_file(db, file)
    return None


# ============================================================
# 共享授权
# ============================================================
@router.post(
    "/{file_id}/shares",
    response_model=schemas.Message,
    summary="共享文件给指定用户",
)
def add_share(
    file_id: int,
    body: schemas.ShareCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    file = crud.file.get_file(db, file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="文件不存在")
    if file.owner_id != user.id:
        raise HTTPException(status_code=403, detail="仅 owner 可共享")
    if not crud.file.get_user(db, body.shared_with_user_id):
        raise HTTPException(status_code=400, detail="目标用户不存在")
    # 共享时自动切换为 shared 可见性
    if file.visibility != "shared":
        crud.file.update_visibility(db, file, "shared")
    try:
        crud.file.add_share(db, file_id, body.shared_with_user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": f"已共享给用户 {body.shared_with_user_id}"}


@router.delete(
    "/{file_id}/shares/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="取消共享",
)
def remove_share(
    file_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    file = crud.file.get_file(db, file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="文件不存在")
    if file.owner_id != user.id:
        raise HTTPException(status_code=403, detail="仅 owner 可取消共享")
    crud.file.remove_share(db, file_id, user_id)
    return None
