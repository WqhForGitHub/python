"""Pydantic 模型 (Schema)。

用于：
1. 请求体校验（注册 / 登录 / 更新 / 分配角色权限等）
2. 响应模型序列化，避免暴露 password_hash 等敏感字段
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ============================================================
# 认证相关
# ============================================================
class UserRegister(BaseModel):
    """注册请求体。"""

    username: str = Field(
        ...,
        min_length=3,
        max_length=20,
        pattern=r"^[A-Za-z0-9_]+$",
        description="用户名，3-20 位字母数字下划线",
        examples=["alice"],
    )
    email: EmailStr = Field(..., description="邮箱地址", examples=["alice@example.com"])
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


class UserLogin(BaseModel):
    """登录请求体（用户名或邮箱均可）。"""

    username: str = Field(..., description="用户名或邮箱", examples=["alice"])
    password: str = Field(..., description="密码", examples=["Secret123"])


class TokenPair(BaseModel):
    """登录 / 刷新成功后返回的令牌对。"""

    access_token: str = Field(..., description="访问令牌，有效期较短")
    refresh_token: str = Field(
        ..., description="刷新令牌，有效期较长，用于换取新的令牌对"
    )
    token_type: str = Field("bearer", description="令牌类型")
    expires_in: int = Field(..., description="access_token 有效期（秒）")


class RefreshRequest(BaseModel):
    """刷新令牌请求体。"""

    refresh_token: str = Field(..., description="刷新令牌")


class Message(BaseModel):
    """通用消息响应。"""

    message: str


# ============================================================
# 权限 / 角色
# ============================================================
class PermissionRead(BaseModel):
    id: int
    code: str
    name: str
    description: str

    model_config = ConfigDict(from_attributes=True)


class RoleRead(BaseModel):
    id: int
    name: str
    description: str

    model_config = ConfigDict(from_attributes=True)


class RoleDetail(RoleRead):
    """角色详情（含权限列表）。"""

    permissions: list[PermissionRead] = []

    model_config = ConfigDict(from_attributes=True)


class RoleCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        pattern=r"^[A-Za-z0-9_]+$",
        description="角色名，2-50 位字母数字下划线",
        examples=["editor"],
    )
    description: str = Field("", max_length=255, description="角色描述")


class RoleUpdate(BaseModel):
    description: Optional[str] = Field(None, max_length=255, description="角色描述")


class AssignPermissions(BaseModel):
    permission_ids: list[int] = Field(..., min_length=1, description="权限 ID 列表")


class PermissionCreate(BaseModel):
    code: str = Field(
        ...,
        min_length=2,
        max_length=64,
        pattern=r"^[a-z]+:[a-z_]+$",
        description="权限编码，格式如 user:read",
        examples=["article:read"],
    )
    name: str = Field(..., min_length=2, max_length=100, description="权限名称")
    description: str = Field("", max_length=255, description="权限描述")


# ============================================================
# 用户
# ============================================================
class UserRead(BaseModel):
    """用户响应模型（不含密码）。"""

    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    roles: list[RoleRead] = []

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """更新用户请求体（所有字段可选）。"""

    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    password: Optional[str] = Field(
        None, min_length=6, max_length=32, description="新密码"
    )
    is_active: Optional[bool] = Field(None, description="是否启用")

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


class AssignRoles(BaseModel):
    role_ids: list[int] = Field(
        ..., min_length=1, description="角色 ID 列表（全量覆盖）"
    )
