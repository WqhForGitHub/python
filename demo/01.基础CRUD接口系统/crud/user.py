"""用户 CRUD 操作。"""

from sqlalchemy.orm import Session

import models
import schemas


def get_user(db: Session, user_id: int) -> models.User | None:
    """根据 ID 查询单个用户。"""
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> models.User | None:
    """根据用户名查询用户（用于唯一性校验）。"""
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str) -> models.User | None:
    """根据邮箱查询用户（用于唯一性校验）。"""
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 20) -> list[models.User]:
    """查询用户列表（分页）。"""
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user_in: schemas.UserCreate) -> models.User:
    """创建用户。"""
    db_user = models.User(
        username=user_in.username,
        email=user_in.email,
        password=user_in.password,  # 演示用，生产环境请哈希存储
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(
    db: Session, db_user: models.User, user_in: schemas.UserUpdate
) -> models.User:
    """更新用户。仅更新请求体中非 None 的字段。"""
    update_data = user_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, db_user: models.User) -> None:
    """删除用户。关联的文章通过 cascade 一并删除。"""
    db.delete(db_user)
    db.commit()
