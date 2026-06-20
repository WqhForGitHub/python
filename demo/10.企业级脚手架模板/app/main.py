"""FastAPI 应用入口（工厂风格）。

启动方式：
    uvicorn app.main:app --reload

企业级脚手架：
- 分层架构：api -> service -> repository -> model
- 异步 SQLAlchemy（PostgreSQL / SQLite 降级）
- Redis（可选）
- JWT + RBAC
- 统一响应包装 + 全局异常处理
- 版本化路由（/api/v1）
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import AsyncSessionLocal, engine
from app.core.exceptions import register_exception_handlers
from app.core.redis import close_redis, get_redis
from app.initial_data import init_data
from app.models import Base  # noqa: F401  确保模型注册


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 建表 + 初始化数据
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        await init_data(db)
    # 预热 Redis（失败不阻断启动）
    await get_redis()
    yield
    await close_redis()
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description=(
            "企业级 FastAPI 脚手架模板 Demo。\n\n"
            "## 架构\n"
            "- **分层架构**：api -> service -> repository -> model\n"
            "- **异步 DB**：PostgreSQL（asyncpg），可降级 SQLite（aiosqlite）\n"
            "- **Redis**：可选，token / 缓存\n"
            "- **JWT + RBAC**：用户 - 角色 - 权限三级\n"
            "- **统一响应**：`{code,message,data}` 包装\n"
            "- **版本路由**：`/api/v1/*`\n\n"
            "## 默认账号\n"
            f"| 用户名 | 密码 | 角色 |\n| --- | --- | --- |\n"
            f"| {settings.INITIAL_ADMIN_USERNAME} | {settings.INITIAL_ADMIN_PASSWORD} | admin（超级管理员） |"
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    register_exception_handlers(app)

    @app.get("/", tags=["默认"], summary="健康检查")
    def root():
        return {"app": settings.APP_NAME, "env": settings.APP_ENV, "docs": "/docs"}

    @app.get("/health", tags=["默认"], summary="健康检查")
    def health():
        return {"status": "ok"}

    app.include_router(api_router)
    return app


app = create_app()
