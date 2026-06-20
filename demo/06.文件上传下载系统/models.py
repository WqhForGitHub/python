"""SQLAlchemy ORM 模型。

FileRecord 记录文件元数据 + 权限信息。
文件二进制存储在对象存储（本地 / MinIO），数据库仅存路径 / key。
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    files = relationship("FileRecord", back_populates="owner", cascade="all, delete-orphan")


class FileRecord(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)        # 原始文件名
    stored_key = Column(String(255), unique=True, nullable=False)  # 存储后端中的 key
    content_type = Column(String(100), default="", nullable=False)
    size = Column(Integer, nullable=False)                # 字节
    # sha256 校验，可用于去重
    checksum = Column(String(64), default="", nullable=False)

    # 权限：public（公开）/ private（仅 owner）/ shared（owner + shared_with）
    visibility = Column(String(20), default="private", nullable=False)

    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    owner = relationship("User", back_populates="files")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class FileShare(Base):
    """文件共享授权（visibility=shared 时生效）。"""

    __tablename__ = "file_shares"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    shared_with_user_id = Column(Integer, nullable=False)

    file = relationship("FileRecord")
