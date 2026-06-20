"""用户 CRUD 操作（异步）。"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import models
import schemas


async def get_user(db: AsyncSession, user_id: int) -> models.User | None:
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    return result.scalar_one_or_none()


async def get_users(db: AsyncSession) -> list[models.User]:
    result = await db.execute(select(models.User).order_by(models.User.id))
    return list(result.scalars().all())


async def create_user(db: AsyncSession, user_in: schemas.UserCreate) -> models.User:
    user = models.User(
        username=user_in.username,
        email=user_in.email,
        bio=user_in.bio,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
