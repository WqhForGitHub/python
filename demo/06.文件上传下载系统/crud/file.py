"""文件元数据 CRUD 操作 + 权限辅助。"""

import hashlib
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

import models
import schemas
import storage


def get_user(db: Session, user_id: int) -> models.User | None:
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> models.User | None:
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, username: str) -> models.User:
    user = models.User(username=username)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_file(db: Session, file_id: int) -> models.FileRecord | None:
    return db.query(models.FileRecord).filter(models.FileRecord.id == file_id).first()


def list_files_by_owner(
    db: Session, owner_id: int, skip: int = 0, limit: int = 50
) -> list[models.FileRecord]:
    return (
        db.query(models.FileRecord)
        .filter(models.FileRecord.owner_id == owner_id)
        .order_by(models.FileRecord.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def list_public_files(
    db: Session, skip: int = 0, limit: int = 50
) -> list[models.FileRecord]:
    return (
        db.query(models.FileRecord)
        .filter(models.FileRecord.visibility == "public")
        .order_by(models.FileRecord.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def generate_stored_key(filename: str) -> str:
    """按 年/月 生成存储 key，避免单目录文件过多。"""
    now = datetime.utcnow()
    ext = "".join(Path(filename).suffix.split(".")[-1:]) if "." in filename else ""
    # 用 uuid 保证唯一，保留扩展名便于内容类型推断
    return f"{now.strftime('%Y/%m')}/{uuid4().hex}{ext}"


# 单独导入 Path 供上方使用
from pathlib import Path  # noqa: E402


def save_upload(
    db: Session,
    owner_id: int,
    filename: str,
    data: bytes,
    content_type: str,
    visibility: str = "private",
) -> models.FileRecord:
    key = generate_stored_key(filename)
    storage.save(key, data)
    checksum = hashlib.sha256(data).hexdigest()

    record = models.FileRecord(
        filename=filename,
        stored_key=key,
        content_type=content_type,
        size=len(data),
        checksum=checksum,
        visibility=visibility,
        owner_id=owner_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_visibility(
    db: Session, file: models.FileRecord, visibility: str
) -> models.FileRecord:
    file.visibility = visibility
    db.commit()
    db.refresh(file)
    return file


def delete_file(db: Session, file: models.FileRecord) -> None:
    # 先删对象存储，再删数据库记录
    storage.delete(file.stored_key)
    db.delete(file)
    db.commit()


# ------------------------------------------------------------
# 共享授权
# ------------------------------------------------------------
def is_shared_with(db: Session, file_id: int, user_id: int) -> bool:
    return (
        db.query(models.FileShare)
        .filter(
            models.FileShare.file_id == file_id,
            models.FileShare.shared_with_user_id == user_id,
        )
        .first()
        is not None
    )


def add_share(db: Session, file_id: int, user_id: int) -> models.FileShare:
    if is_shared_with(db, file_id, user_id):
        raise ValueError("已共享给该用户")
    share = models.FileShare(file_id=file_id, shared_with_user_id=user_id)
    db.add(share)
    db.commit()
    db.refresh(share)
    return share


def remove_share(db: Session, file_id: int, user_id: int) -> None:
    share = (
        db.query(models.FileShare)
        .filter(
            models.FileShare.file_id == file_id,
            models.FileShare.shared_with_user_id == user_id,
        )
        .first()
    )
    if share:
        db.delete(share)
        db.commit()
