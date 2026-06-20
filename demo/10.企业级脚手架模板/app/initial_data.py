"""初始化默认数据：权限 / 角色 / 管理员。幂等。"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models.role import Permission, Role
from app.models.user import User

DEFAULT_PERMISSIONS = [
    ("user:read",        "查看用户",   "查看用户列表与详情"),
    ("user:write",       "编辑用户",   "修改用户信息"),
    ("user:delete",      "删除用户",   "删除用户"),
    ("user:assign_role", "分配角色",   "为用户分配角色"),
    ("role:read",        "查看角色",   "查看角色"),
    ("role:write",       "编辑角色",   "创建 / 修改角色"),
]
USER_ROLE_PERMISSIONS = ["user:read"]


async def init_data(db: AsyncSession) -> None:
    await _init_permissions(db)
    await _init_roles(db)
    await _init_admin(db)


async def _init_permissions(db: AsyncSession) -> None:
    for code, name, desc in DEFAULT_PERMISSIONS:
        existing = (
            await db.execute(select(Permission).where(Permission.code == code))
        ).scalar_one_or_none()
        if not existing:
            db.add(Permission(code=code, name=name, description=desc))
    await db.commit()


async def _init_roles(db: AsyncSession) -> None:
    # admin 角色：全部权限
    admin = (await db.execute(select(Role).where(Role.name == "admin"))).scalar_one_or_none()
    if not admin:
        admin = Role(name="admin", description="超级管理员")
        admin.permissions = (await db.execute(select(Permission))).scalars().all()
        db.add(admin)

    user_role = (await db.execute(select(Role).where(Role.name == "user"))).scalar_one_or_none()
    if not user_role:
        user_role = Role(name="user", description="普通用户")
        user_role.permissions = (
            (
                await db.execute(
                    select(Permission).where(Permission.code.in_(USER_ROLE_PERMISSIONS))
                )
            )
            .scalars()
            .all()
        )
        db.add(user_role)
    await db.commit()


async def _init_admin(db: AsyncSession) -> None:
    admin = (
        await db.execute(
            select(User).where(User.username == settings.INITIAL_ADMIN_USERNAME)
        )
    ).scalar_one_or_none()
    if admin:
        return
    admin = User(
        username=settings.INITIAL_ADMIN_USERNAME,
        email=settings.INITIAL_ADMIN_EMAIL,
        password_hash=hash_password(settings.INITIAL_ADMIN_PASSWORD),
        is_superuser=True,
    )
    admin_role = (
        await db.execute(select(Role).where(Role.name == "admin"))
    ).scalar_one_or_none()
    if admin_role:
        admin.roles = [admin_role]
    db.add(admin)
    await db.commit()
