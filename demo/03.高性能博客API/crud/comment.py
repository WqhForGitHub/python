"""评论 CRUD 操作（异步）。"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import models
import schemas


async def get_comment(db: AsyncSession, comment_id: int) -> models.Comment | None:
    result = await db.execute(
        select(models.Comment).where(models.Comment.id == comment_id)
    )
    return result.scalar_one_or_none()


async def list_comments_by_post(
    db: AsyncSession, post_id: int
) -> list[models.Comment]:
    result = await db.execute(
        select(models.Comment)
        .where(models.Comment.post_id == post_id)
        .order_by(models.Comment.created_at)
    )
    return list(result.scalars().all())


async def create_comment(
    db: AsyncSession, post_id: int, comment_in: schemas.CommentCreate
) -> models.Comment:
    comment = models.Comment(
        content=comment_in.content,
        post_id=post_id,
        author_id=comment_in.author_id,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment


async def delete_comment(db: AsyncSession, comment: models.Comment) -> None:
    await db.delete(comment)
    await db.commit()
