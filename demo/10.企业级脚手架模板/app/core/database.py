"""异步数据库引擎 / Session。

默认 PostgreSQL（asyncpg）；DATABASE_URL 为 sqlite 时使用 aiosqlite，
便于本地无 PG 环境快速运行 Demo。
"""
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.is_sqlite else {}
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_DEBUG and settings.APP_ENV == "development",
    connect_args=connect_args,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """异步 DB 依赖。"""
    async with AsyncSessionLocal() as db:
        yield db
