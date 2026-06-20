"""角色 / 权限模型。"""
from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin

# 角色 - 权限（多对多）
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class Permission(IDMixin, TimestampMixin, Base):
    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)

    roles: Mapped[list["Role"]] = relationship(
        "Role", secondary=role_permissions, back_populates="permissions"
    )


class Role(IDMixin, TimestampMixin, Base):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)

    users: Mapped[list["User"]] = relationship(  # noqa: F821
        "User", secondary="user_roles", back_populates="roles"
    )
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission", secondary=role_permissions, back_populates="roles"
    )
