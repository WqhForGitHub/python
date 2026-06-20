"""SQLAlchemy ORM 模型。

包含两个模型：
- User：用户
- Article：文章，外键关联到 User
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(20), unique=True, index=True, nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=False)
    # 仅做演示，生产环境请使用密码哈希 (如 passlib + bcrypt)
    password = Column(String(128), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 一对多：一个用户有多篇文章
    articles = relationship(
        "Article",
        back_populates="author",
        cascade="all, delete-orphan",
    )


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False, index=True)
    content = Column(Text, nullable=False)

    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    author = relationship("User", back_populates="articles")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
