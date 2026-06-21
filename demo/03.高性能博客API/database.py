"""异步数据库引擎与 Session 配置。

使用 SQLAlchemy 2.0 异步 API + aiosqlite 驱动：
- create_async_engine / async_sessionmaker / AsyncSession
- 所有查询需使用 await db.execute(select(...)) 风格
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

import config

# 异步引擎。SQLite 需指定 check_same_thread=False
engine = create_async_engine(
    config.SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

# 异步 Session 工厂
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# 所有 ORM 模型的基类（同步 / 异步共用同一基类）
Base = declarative_base()


async def get_db():
    """异步依赖项：每个请求获取一个独立的 AsyncSession，请求结束后关闭。"""
    async with AsyncSessionLocal() as db:
        yield db
