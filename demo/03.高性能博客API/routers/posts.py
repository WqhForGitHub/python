"""文章路由。

支持：
- 创建 / 更新 / 删除 / 查询详情（浏览量自增）
- 分页列表（支持按标签 / 作者 / 关键词筛选）
- 评论创建 / 删除
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

import crud.comment
import crud.post
import crud.user
import schemas
from database import get_db

router = APIRouter(prefix="/posts", tags=["文章"])


@router.post(
    "/",
    response_model=schemas.PostRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建文章",
)
async def create_post(post_in: schemas.PostCreate, db: AsyncSession = Depends(get_db)):
    if not await crud.user.get_user(db, post_in.author_id):
        raise HTTPException(status_code=400, detail=f"作者 ID {post_in.author_id} 不存在")
    return await crud.post.create_post(db, post_in)


@router.get(
    "/",
    summary="文章列表（分页）",
)
async def list_posts(
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    tag_id: int | None = Query(None, description="按标签 ID 筛选"),
    author_id: int | None = Query(None, description="按作者 ID 筛选"),
    keyword: str | None = Query(None, description="标题关键词模糊匹配"),
    db: AsyncSession = Depends(get_db),
):
    items, total = await crud.post.get_posts(
        db, page=page, size=size, tag_id=tag_id, author_id=author_id, keyword=keyword
    )
    pages = (total + size - 1) // size if total else 0
    return {
        "items": items,
        "meta": {"page": page, "size": size, "total": total, "pages": pages},
    }


@router.get(
    "/{post_id}",
    response_model=schemas.PostRead,
    summary="文章详情（浏览量 +1）",
)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    post = await crud.post.get_post(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail=f"文章 ID {post_id} 不存在")
    await crud.post.increment_view(db, post_id)
    # 刷新以拿到最新 view_count
    await db.refresh(post)
    return post


@router.put(
    "/{post_id}",
    response_model=schemas.PostRead,
    summary="更新文章",
)
async def update_post(
    post_id: int,
    post_in: schemas.PostUpdate,
    db: AsyncSession = Depends(get_db),
):
    post = await crud.post.get_post(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail=f"文章 ID {post_id} 不存在")
    return await crud.post.update_post(db, post, post_in)


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除文章",
)
async def delete_post(post_id: int, db: AsyncSession = Depends(get_db)):
    post = await crud.post.get_post(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail=f"文章 ID {post_id} 不存在")
    await crud.post.delete_post(db, post)
    return None


# ============================================================
# 评论
# ============================================================
@router.post(
    "/{post_id}/comments",
    response_model=schemas.CommentRead,
    status_code=status.HTTP_201_CREATED,
    summary="发表评论",
)
async def create_comment(
    post_id: int,
    comment_in: schemas.CommentCreate,
    db: AsyncSession = Depends(get_db),
):
    if not await crud.post.get_post(db, post_id):
        raise HTTPException(status_code=404, detail=f"文章 ID {post_id} 不存在")
    if not await crud.user.get_user(db, comment_in.author_id):
        raise HTTPException(status_code=400, detail=f"评论者 ID {comment_in.author_id} 不存在")
    return await crud.comment.create_comment(db, post_id, comment_in)


@router.delete(
    "/{post_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除评论",
)
async def delete_comment(
    post_id: int,
    comment_id: int,
    db: AsyncSession = Depends(get_db),
):
    comment = await crud.comment.get_comment(db, comment_id)
    if comment is None or comment.post_id != post_id:
        raise HTTPException(status_code=404, detail="评论不存在")
    await crud.comment.delete_comment(db, comment)
    return None
