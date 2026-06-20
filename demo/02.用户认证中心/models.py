"""SQLAlchemy ORM 模型。

采用经典 RBAC（Role-Based Access Control）结构：

    User  <--多对多-->  Role  <--多对多-->  Permission

另外 RefreshToken 表用于持久化刷新令牌，支持令牌轮转与吊销（登出）。
"""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
)
from sqlalchemy.orm import relationship

from database import Base


# ------------------------------------------------------------------
# 关联表（多对多）
# ------------------------------------------------------------------
# 用户 - 角色
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

# 角色 - 权限
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


# ------------------------------------------------------------------
# 用户
# ------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(20), unique=True, index=True, nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    roles = relationship("Role", secondary=user_roles, back_populates="users")
    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )


# ------------------------------------------------------------------
# 角色
# ------------------------------------------------------------------
class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(255), default="", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")


# ------------------------------------------------------------------
# 权限
# ------------------------------------------------------------------
class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(64), unique=True, index=True, nullable=False)  # 如 user:read
    name = Column(String(100), nullable=False)                          # 人类可读名称
    description = Column(String(255), default="", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")


# ------------------------------------------------------------------
# 刷新令牌
# ------------------------------------------------------------------
class RefreshToken(Base):
    """持久化 refresh token，用于：

    1. 校验 refresh token 是否有效 / 是否已被吊销
    2. 令牌轮转（refresh 时吊销旧令牌，签发新令牌）
    3. 登出时吊销令牌
    """

    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    jti = Column(String(64), unique=True, index=True, nullable=False)        # JWT ID
    token_hash = Column(String(255), unique=True, index=True, nullable=False)  # 哈希后存储
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="refresh_tokens")
