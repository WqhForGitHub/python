"""初始化默认数据：权限、角色、管理员账号。

应用首次启动时调用，已存在则跳过（幂等）。

默认账号：
    用户名：admin    密码：Admin123456    （拥有全部权限）
    用户名：alice    密码：Alice123456    （普通用户，仅 article 相关权限）

可通过环境变量覆盖管理员账号密码（见 config.py）。
"""
from sqlalchemy.orm import Session

import config
import crud.permission
import crud.role
import crud.user
import models
from database import SessionLocal
from security import hash_password


# 预置权限：(code, name, description)
DEFAULT_PERMISSIONS = [
    ("user:read",         "查看用户",   "查看用户列表与详情"),
    ("user:write",        "编辑用户",   "修改用户信息"),
    ("user:delete",       "删除用户",   "删除用户"),
    ("user:assign_role",  "分配角色",   "为用户分配或移除角色"),
    ("role:read",         "查看角色",   "查看角色列表与详情"),
    ("role:write",        "编辑角色",   "创建与修改角色、分配权限"),
    ("role:delete",       "删除角色",   "删除角色"),
    ("permission:manage", "管理权限",   "创建与查看权限"),
    ("article:read",      "查看文章",   "查看文章（示例受保护资源）"),
    ("article:write",     "编辑文章",   "创建与修改文章（示例受保护资源）"),
]

# 普通用户角色拥有的权限
USER_ROLE_PERMISSIONS = ["article:read", "article:write"]


def init_db() -> None:
    """初始化默认数据。幂等，可重复调用。"""
    db = SessionLocal()
    try:
        _init_permissions(db)
        _init_roles(db)
        _init_admin(db)
    finally:
        db.close()


def _init_permissions(db: Session) -> None:
    for code, name, desc in DEFAULT_PERMISSIONS:
        if not crud.permission.get_permission_by_code(db, code):
            db.add(models.Permission(code=code, name=name, description=desc))
    db.commit()


def _init_roles(db: Session) -> None:
    # admin 角色：拥有所有权限
    if not crud.role.get_role_by_name(db, "admin"):
        admin = models.Role(name="admin", description="超级管理员，拥有全部权限")
        admin.permissions = db.query(models.Permission).all()
        db.add(admin)

    # user 角色：仅基本权限
    if not crud.role.get_role_by_name(db, config.DEFAULT_ROLE_NAME):
        user_role = models.Role(name=config.DEFAULT_ROLE_NAME, description="普通用户")
        user_role.permissions = (
            db.query(models.Permission)
            .filter(models.Permission.code.in_(USER_ROLE_PERMISSIONS))
            .all()
        )
        db.add(user_role)

    db.commit()


def _init_admin(db: Session) -> None:
    if crud.user.get_user_by_username(db, config.INITIAL_ADMIN_USERNAME):
        return
    admin = models.User(
        username=config.INITIAL_ADMIN_USERNAME,
        email=config.INITIAL_ADMIN_EMAIL,
        password_hash=hash_password(config.INITIAL_ADMIN_PASSWORD),
    )
    admin_role = crud.role.get_role_by_name(db, "admin")
    if admin_role:
        admin.roles.append(admin_role)
    db.add(admin)

    # 顺便创建一个普通用户用于演示
    if not crud.user.get_user_by_username(db, "alice"):
        alice = models.User(
            username="alice",
            email="alice@example.com",
            password_hash=hash_password("Alice123456"),
        )
        user_role = crud.role.get_role_by_name(db, config.DEFAULT_ROLE_NAME)
        if user_role:
            alice.roles.append(user_role)
        db.add(alice)

    db.commit()
