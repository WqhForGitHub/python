"""FastAPI 应用入口。

启动方式：
    uvicorn main:app --reload

使用异步 SQLAlchemy（aiosqlite）实现高性能博客 API。
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

import models
from database import engine
from routers import posts, tags, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时建表。"""
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="高性能博客API",
    description=(
        "基于 FastAPI + 异步 SQLAlchemy (aiosqlite) 的博客 API Demo。\n\n"
        "## 功能特性\n"
        "- **异步数据库**：SQLAlchemy 2.0 async API\n"
        "- **标签系统**：多对多标签关联\n"
        "- **评论系统**：文章一对多评论\n"
        "- **API 分页**：页码 / 每页数量，支持按标签 / 作者 / 关键词筛选\n"
        "- **浏览量统计**：使用 UPDATE ... SET view_count = view_count + 1 避免竞争"
    ),
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", tags=["默认"], summary="欢迎页")
def root():
    return {"message": "欢迎使用高性能博客API", "docs": "/docs", "redoc": "/redoc"}


# 注册路由
app.include_router(users.router)
app.include_router(tags.router)
app.include_router(posts.router)
