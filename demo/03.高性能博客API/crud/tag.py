"""标签 CRUD 操作（异步）。"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import models
import schemas


async def get_tag(db: AsyncSession, tag_id: int) -> models.Tag | None:
    result = await db.execute(select(models.Tag).where(models.Tag.id == tag_id))
    return result.scalar_one_or_none()


async def get_tag_by_name(db: AsyncSession, name: str) -> models.Tag | None:
    result = await db.execute(select(models.Tag).where(models.Tag.name == name))
    return result.scalar_one_or_none()


async def get_tags(db: AsyncSession) -> list[models.Tag]:
    result = await db.execute(select(models.Tag).order_by(models.Tag.name))
    return list(result.scalars().all())


async def create_tag(db: AsyncSession, tag_in: schemas.TagCreate) -> models.Tag:
    tag = models.Tag(name=tag_in.name)
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


async def delete_tag(db: AsyncSession, tag: models.Tag) -> None:
    await db.delete(tag)
    await db.commit()
