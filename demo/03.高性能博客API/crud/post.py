"""文章 CRUD 操作（异步）。

包含分页查询、按标签筛选、浏览量自增等功能。
"""
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
import schemas


async def get_post(db: AsyncSession, post_id: int) -> models.Post | None:
    """获取文章详情（含标签与评论）。"""
    result = await db.execute(
        select(models.Post)
        .options(
            selectinload(models.Post.tags),
            selectinload(models.Post.comments),
        )
        .where(models.Post.id == post_id)
    )
    return result.scalar_one_or_none()


async def get_posts(
    db: AsyncSession,
    page: int = 1,
    size: int = 10,
    tag_id: int | None = None,
    author_id: int | None = None,
    keyword: str | None = None,
) -> tuple[list[models.Post], int]:
    """分页查询文章列表。

    返回 (items, total)。支持按标签 / 作者 / 关键词（标题模糊）筛选。
    """
    stmt = select(models.Post).options(selectinload(models.Post.tags))

    if tag_id is not None:
        stmt = stmt.join(models.Post.tags).where(models.Tag.id == tag_id)
    if author_id is not None:
        stmt = stmt.where(models.Post.author_id == author_id)
    if keyword:
        stmt = stmt.where(models.Post.title.like(f"%{keyword}%"))

    # 总数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    # 分页（按创建时间倒序）
    stmt = stmt.order_by(models.Post.created_at.desc())
    stmt = stmt.offset((page - 1) * size).limit(size)
    items = list((await db.execute(stmt)).scalars().all())
    return items, total


async def create_post(db: AsyncSession, post_in: schemas.PostCreate) -> models.Post:
    post = models.Post(
        title=post_in.title,
        content=post_in.content,
        is_published=1 if post_in.is_published else 0,
        author_id=post_in.author_id,
    )
    # 关联标签
    if post_in.tag_ids:
        tags = (
            (await db.execute(select(models.Tag).where(models.Tag.id.in_(post_in.tag_ids))))
            .scalars()
            .all()
        )
        post.tags = list(tags)

    db.add(post)
    await db.commit()
    await db.refresh(post)
    # 重新加载以填充 tags 关系
    await db.refresh(post, attribute_names=["tags"])
    return post


async def update_post(
    db: AsyncSession,
    post: models.Post,
    post_in: schemas.PostUpdate,
) -> models.Post:
    update_data = post_in.model_dump(exclude_unset=True)
    tag_ids = update_data.pop("tag_ids", None)

    if "is_published" in update_data:
        update_data["is_published"] = 1 if update_data["is_published"] else 0

    for field, value in update_data.items():
        setattr(post, field, value)

    if tag_ids is not None:
        tags = (
            (await db.execute(select(models.Tag).where(models.Tag.id.in_(tag_ids))))
            .scalars()
            .all()
        )
        post.tags = list(tags)

    await db.commit()
    await db.refresh(post)
    await db.refresh(post, attribute_names=["tags"])
    return post


async def delete_post(db: AsyncSession, post: models.Post) -> None:
    await db.delete(post)
    await db.commit()


async def increment_view(db: AsyncSession, post_id: int) -> None:
    """浏览量自增（避免读改写竞争）。"""
    await db.execute(
        update(models.Post).where(models.Post.id == post_id).values(
            view_count=models.Post.view_count + 1
        )
    )
    await db.commit()
