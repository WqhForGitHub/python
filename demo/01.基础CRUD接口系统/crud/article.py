"""文章 CRUD 操作。"""
from sqlalchemy.orm import Session

import models
import schemas


def get_article(db: Session, article_id: int) -> models.Article | None:
    """根据 ID 查询单个文章。"""
    return db.query(models.Article).filter(models.Article.id == article_id).first()


def get_articles(db: Session, skip: int = 0, limit: int = 20) -> list[models.Article]:
    """查询文章列表（分页），按创建时间倒序。"""
    return (
        db.query(models.Article)
        .order_by(models.Article.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_article(db: Session, article_in: schemas.ArticleCreate) -> models.Article:
    """创建文章。需保证 author_id 对应的用户存在（路由层校验）。"""
    db_article = models.Article(
        title=article_in.title,
        content=article_in.content,
        author_id=article_in.author_id,
    )
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article


def update_article(
    db: Session,
    db_article: models.Article,
    article_in: schemas.ArticleUpdate,
) -> models.Article:
    """更新文章。仅更新请求体中非 None 的字段。"""
    update_data = article_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_article, field, value)
    db.commit()
    db.refresh(db_article)
    return db_article


def delete_article(db: Session, db_article: models.Article) -> None:
    """删除文章。"""
    db.delete(db_article)
    db.commit()
