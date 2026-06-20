"""用户 CRUD 操作。"""
from sqlalchemy.orm import Session

import models
import schemas
from security import hash_password


def get_user(db: Session, user_id: int) -> models.User | None:
    """根据 ID 查询单个用户。"""
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> models.User | None:
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_login(db: Session, login: str) -> models.User | None:
    """根据用户名或邮箱查询用户（登录时使用）。"""
    return (
        db.query(models.User)
        .filter((models.User.username == login) | (models.User.email == login))
        .first()
    )


def get_users(db: Session, skip: int = 0, limit: int = 20) -> list[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user_in: schemas.UserRegister) -> models.User:
    db_user = models.User(
        username=user_in.username,
        email=user_in.email,
        password_hash=hash_password(user_in.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, db_user: models.User, user_in: schemas.UserUpdate) -> models.User:
    """更新用户，仅更新请求体中非 None 的字段。"""
    update_data = user_in.model_dump(exclude_unset=True)
    # 密码需哈希后存储
    if update_data.get("password"):
        update_data["password_hash"] = hash_password(update_data.pop("password"))
    else:
        update_data.pop("password", None)

    for field, value in update_data.items():
        setattr(db_user, field, value)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, db_user: models.User) -> None:
    db.delete(db_user)
    db.commit()


def set_roles(db: Session, user: models.User, role_ids: list[int]) -> models.User:
    """全量覆盖用户的角色。"""
    from crud.role import get_roles_by_ids

    user.roles = get_roles_by_ids(db, role_ids)
    db.commit()
    db.refresh(user)
    return user


# ------------------------------------------------------------------
# RBAC 辅助：从已加载的用户对象收集角色与权限
# ------------------------------------------------------------------
def collect_role_names(user: models.User) -> set[str]:
    return {r.name for r in user.roles}


def collect_permissions(user: models.User) -> set[str]:
    perms: set[str] = set()
    for role in user.roles:
        for perm in role.permissions:
            perms.add(perm.code)
    return perms
