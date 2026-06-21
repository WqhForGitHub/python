"""user-service CRUD 操作。

包含 verify_password 接口供 auth-service 远程调用验证凭据。
"""

from sqlalchemy.orm import Session

import models
import shared.models as schemas
from models import hash_password, verify_password


def get_user(db: Session, user_id: int) -> models.User | None:
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> models.User | None:
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.query(models.User).filter(models.User.email == email).first()


def list_users(db: Session, skip: int = 0, limit: int = 50) -> list[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user_in: schemas.UserCreate) -> models.User:
    user = models.User(
        username=user_in.username,
        email=user_in.email,
        password_hash=hash_password(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def verify_credentials(db: Session, username: str, password: str) -> models.User | None:
    """供 auth-service 远程调用：验证用户名 + 密码。"""
    user = get_user_by_username(db, username)
    if user and verify_password(password, user.password_hash):
        return user
    return None
