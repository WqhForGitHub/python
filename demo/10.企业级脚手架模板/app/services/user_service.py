"""用户业务：查询 / 更新 / 删除 / 分配角色。"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.user import User
from app.repositories.user import RoleRepository, UserRepository
from app.schemas.user import AssignRoles, UserUpdate


async def get_user(db: AsyncSession, user_id: int) -> User:
    repo = UserRepository(db)
    user = await repo.get_with_roles(user_id)
    if user is None:
        raise NotFoundError(f"用户 ID {user_id} 不存在")
    return user


async def list_users(db: AsyncSession, skip: int = 0, limit: int = 50) -> list[User]:
    repo = UserRepository(db)
    return await repo.list_with_roles(skip, limit)


async def update_user(db: AsyncSession, user_id: int, data: UserUpdate) -> User:
    repo = UserRepository(db)
    user = await repo.get(user_id)
    if user is None:
        raise NotFoundError(f"用户 ID {user_id} 不存在")
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user_id: int) -> None:
    repo = UserRepository(db)
    user = await repo.get(user_id)
    if user is None:
        raise NotFoundError(f"用户 ID {user_id} 不存在")
    await repo.delete(user)


async def assign_roles(db: AsyncSession, user_id: int, data: AssignRoles) -> User:
    user_repo = UserRepository(db)
    role_repo = RoleRepository(db)
    user = await user_repo.get(user_id)
    if user is None:
        raise NotFoundError(f"用户 ID {user_id} 不存在")
    roles = await role_repo.get_by_ids(data.role_ids)
    if len(roles) != len(data.role_ids):
        raise NotFoundError("部分角色 ID 不存在")
    return await user_repo.set_roles(user, roles)


def collect_permissions(user: User) -> set[str]:
    perms: set[str] = set()
    for role in user.roles:
        for perm in role.permissions:
            perms.add(perm.code)
    return perms
