"""Pydantic 模型 (Schema)。

用于请求体校验与响应序列化。
"""

from datetime import datetime
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field

T = TypeVar("T")


# ============================================================
# 通用
# ============================================================
class PageParams(BaseModel):
    """分页参数（通过 Query 解析，非请求体）。"""

    page: int = Field(1, ge=1, description="页码，从 1 开始")
    size: int = Field(10, ge=1, le=100, description="每页数量")


class PageMeta(BaseModel):
    """分页元数据。"""

    page: int
    size: int
    total: int
    pages: int


class Page(BaseModel, Generic[T]):
    """通用分页响应。"""

    items: list[T]
    meta: PageMeta


# ============================================================
# 用户
# ============================================================
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, examples=["alice"])
    email: EmailStr = Field(..., examples=["alice@example.com"])
    bio: str = Field("", max_length=255, description="个人简介")


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    bio: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# 标签
# ============================================================
class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=30, examples=["FastAPI"])


class TagRead(BaseModel):
    id: int
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# 文章
# ============================================================
class PostBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, examples=["FastAPI 异步指南"])
    content: str = Field(..., min_length=1, examples=["正文内容..."])
    is_published: bool = Field(True, description="是否发布（False 为草稿）")


class PostCreate(PostBase):
    author_id: int = Field(..., gt=0, examples=[1])
    tag_ids: list[int] = Field([], description="标签 ID 列表")


class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    is_published: Optional[bool] = None
    tag_ids: Optional[list[int]] = None


class CommentRead(BaseModel):
    id: int
    content: str
    post_id: int
    author_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PostRead(BaseModel):
    """文章详情（含标签与评论）。"""

    id: int
    title: str
    content: str
    is_published: bool
    view_count: int
    author_id: int
    created_at: datetime
    updated_at: datetime
    tags: list[TagRead] = []
    comments: list[CommentRead] = []

    model_config = ConfigDict(from_attributes=True)


class PostListItem(BaseModel):
    """文章列表项（轻量，不含评论）。"""

    id: int
    title: str
    is_published: bool
    view_count: int
    author_id: int
    created_at: datetime
    tags: list[TagRead] = []

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# 评论
# ============================================================
class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000, examples=["好文！"])
    author_id: int = Field(..., gt=0, examples=[1])
