"""Pydantic 模型 (Schema)。

用于：
1. 请求体校验 (Create / Update)
2. 响应模型序列化 (Read)，避免暴露 password 等敏感字段
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator


# ============================================================
# 用户 Schemas
# ============================================================
class UserBase(BaseModel):
    """用户公共字段。"""

    username: str = Field(
        ...,
        min_length=3,
        max_length=20,
        pattern=r"^[A-Za-z0-9_]+$",
        description="用户名，3-20 位字母数字下划线",
        examples=["alice"],
    )
    email: EmailStr = Field(..., description="邮箱地址", examples=["alice@example.com"])


class UserCreate(UserBase):
    """创建用户请求体。"""

    password: str = Field(
        ...,
        min_length=6,
        max_length=32,
        description="密码，6-32 位，必须同时包含字母和数字",
        examples=["Secret123"],
    )

    @field_validator("password")
    @classmethod
    def password_must_contain_letter_and_digit(cls, v: str) -> str:
        if not any(c.isalpha() for c in v):
            raise ValueError("密码必须至少包含一个字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须至少包含一个数字")
        return v


class UserUpdate(BaseModel):
    """更新用户请求体（所有字段可选）。"""

    username: Optional[str] = Field(
        None,
        min_length=3,
        max_length=20,
        pattern=r"^[A-Za-z0-9_]+$",
        description="用户名",
    )
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    password: Optional[str] = Field(
        None,
        min_length=6,
        max_length=32,
        description="密码",
    )

    @field_validator("password")
    @classmethod
    def password_must_contain_letter_and_digit(cls, v):
        if v is None:
            return v
        if not any(c.isalpha() for c in v):
            raise ValueError("密码必须至少包含一个字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须至少包含一个数字")
        return v


class UserRead(UserBase):
    """用户响应模型（不含密码）。"""

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# 文章 Schemas
# ============================================================
class ArticleBase(BaseModel):
    """文章公共字段。"""

    title: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="文章标题，1-100 个字符",
        examples=["我的第一篇文章"],
    )
    content: str = Field(
        ...,
        min_length=1,
        description="文章正文",
        examples=["Hello FastAPI!"],
    )


class ArticleCreate(ArticleBase):
    """创建文章请求体。"""

    author_id: int = Field(..., gt=0, description="作者用户 ID", examples=[1])


class ArticleUpdate(BaseModel):
    """更新文章请求体（所有字段可选）。"""

    title: Optional[str] = Field(
        None, min_length=1, max_length=100, description="文章标题"
    )
    content: Optional[str] = Field(None, min_length=1, description="文章正文")


class ArticleRead(ArticleBase):
    """文章响应模型。"""

    id: int
    author_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
