"""FastAPI 依赖项：当前用户 + 文件权限校验。

Demo 简化：通过 `X-User-Id` 请求头标识用户。
"""

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

import crud.file
import models
from database import get_db


def get_current_user(
    x_user_id: int | None = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> models.User:
    if x_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请在请求头携带 X-User-Id",
        )
    user = db.query(models.User).filter(models.User.id == x_user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail=f"用户 ID {x_user_id} 不存在")
    return user


def can_access_file(user: models.User, file: models.FileRecord, db: Session) -> bool:
    """权限判断：是否可访问该文件。"""
    if file.visibility == "public":
        return True
    if file.owner_id == user.id:
        return True
    if file.visibility == "shared":
        return crud.file.is_shared_with(db, file.id, user.id)
    return False
