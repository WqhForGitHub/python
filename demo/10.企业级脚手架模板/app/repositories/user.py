"""用户 / 角色 / 权限 仓库。"""

from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.models.role import Permission, Role
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_with_roles(self, id_: int) -> User | None:
        result = await self.db.execute(
            select(User).options(selectinload(User.roles)).where(User.id == id_)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_login(self, login: str) -> User | None:
        result = await self.db.execute(
            select(User).where(or_(User.username == login, User.email == login))
        )
        return result.scalar_one_or_none()

    async def list_with_roles(self, skip: int = 0, limit: int = 50) -> list[User]:
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.roles))
            .offset(skip)
            .limit(limit)
            .order_by(User.id.desc())
        )
        return list(result.scalars().all())

    async def set_roles(self, user: User, roles: list[Role]) -> User:
        user.roles = roles
        await self.db.commit()
        await self.db.refresh(user)
        return user


class RoleRepository(BaseRepository[Role]):
    model = Role

    async def get_by_name(self, name: str) -> Role | None:
        result = await self.db.execute(select(Role).where(Role.name == name))
        return result.scalar_one_or_none()

    async def get_by_ids(self, ids: list[int]) -> list[Role]:
        if not ids:
            return []
        result = await self.db.execute(select(Role).where(Role.id.in_(ids)))
        return list(result.scalars().all())

    async def list_with_permissions(self) -> list[Role]:
        from app.models.role import role_permissions  # noqa: F401
        from sqlalchemy.orm import selectinload as _sol

        result = await self.db.execute(
            select(Role).options(_sol(Role.permissions)).order_by(Role.id)
        )
        return list(result.scalars().all())


class PermissionRepository(BaseRepository[Permission]):
    model = Permission

    async def get_by_code(self, code: str) -> Permission | None:
        result = await self.db.execute(
            select(Permission).where(Permission.code == code)
        )
        return result.scalar_one_or_none()

    async def all_codes(self) -> list[str]:
        result = await self.db.execute(select(Permission.code))
        return list(result.scalars().all())
