"""pytest 配置：使用 SQLite 内存库 + 测试客户端。

运行：
    pip install pytest httpx
    pytest -v
"""
import asyncio
import os
import sys
from pathlib import Path

import pytest
import pytest_asyncio

# 注入项目根到 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 测试使用 SQLite 内存库，覆盖配置
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret"
os.environ["APP_DEBUG"] = "false"

from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.core.database import AsyncSessionLocal, engine  # noqa: E402
from app.initial_data import init_data  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import Base  # noqa: E402


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def client():
    # 每个测试建表 + 初始化数据
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        await init_data(db)

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # 清理
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
