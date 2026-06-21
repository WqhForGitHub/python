"""泛型 Repository 基类，提供通用 CRUD。"""

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """通用异步 CRUD 仓库。

    子类设置 model 属性即可复用通用方法。
    """

    model: type[ModelT]

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self, id_: int) -> ModelT | None:
        result = await self.db.execute(select(self.model).where(self.model.id == id_))
        return result.scalar_one_or_none()

    async def list(self, skip: int = 0, limit: int = 50) -> list[ModelT]:
        result = await self.db.execute(
            select(self.model).offset(skip).limit(limit).order_by(self.model.id.desc())
        )
        return list(result.scalars().all())

    async def add(self, instance: ModelT) -> ModelT:
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def delete(self, instance: ModelT) -> None:
        await self.db.delete(instance)
        await self.db.commit()

    async def commit(self) -> None:
        await self.db.commit()
