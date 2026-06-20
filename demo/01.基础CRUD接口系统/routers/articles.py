"""文章路由。"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import crud.article
import crud.user
import schemas
from database import get_db

router = APIRouter(prefix="/articles", tags=["文章"])


@router.post(
    "/",
    response_model=schemas.ArticleRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建文章",
)
def create_article(article_in: schemas.ArticleCreate, db: Session = Depends(get_db)):
    # 校验作者存在
    if not crud.user.get_user(db, user_id=article_in.author_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"作者 ID {article_in.author_id} 不存在",
        )
    return crud.article.create_article(db, article_in=article_in)


@router.get(
    "/",
    response_model=list[schemas.ArticleRead],
    summary="获取文章列表",
)
def list_articles(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return crud.article.get_articles(db, skip=skip, limit=limit)


@router.get(
    "/{article_id}",
    response_model=schemas.ArticleRead,
    summary="获取文章详情",
)
def get_article(article_id: int, db: Session = Depends(get_db)):
    db_article = crud.article.get_article(db, article_id=article_id)
    if db_article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文章 ID {article_id} 不存在",
        )
    return db_article


@router.put(
    "/{article_id}",
    response_model=schemas.ArticleRead,
    summary="更新文章",
)
def update_article(
    article_id: int,
    article_in: schemas.ArticleUpdate,
    db: Session = Depends(get_db),
):
    db_article = crud.article.get_article(db, article_id=article_id)
    if db_article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文章 ID {article_id} 不存在",
        )
    return crud.article.update_article(db, db_article=db_article, article_in=article_in)


@router.delete(
    "/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除文章",
)
def delete_article(article_id: int, db: Session = Depends(get_db)):
    db_article = crud.article.get_article(db, article_id=article_id)
    if db_article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文章 ID {article_id} 不存在",
        )
    crud.article.delete_article(db, db_article=db_article)
    return None
