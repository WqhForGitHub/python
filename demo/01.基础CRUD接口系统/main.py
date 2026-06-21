"""FastAPI 应用入口。

启动方式：
    uvicorn main:app --reload
"""

from fastapi import FastAPI

import models
from database import engine
from routers import articles, users

# 启动时自动建表（开发环境使用，生产环境推荐使用 Alembic 迁移）
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="基础CRUD接口系统",
    description=(
        "一个使用 FastAPI 实现的基础 CRUD 接口系统 Demo。\n\n"
        "包含 **用户 (User)** 与 **文章 (Article)** 两个资源的增删改查接口，\n"
        "使用 Pydantic 进行请求体校验，FastAPI 自动生成 Swagger / ReDoc 文档。"
    ),
    version="1.0.0",
)


@app.get("/", tags=["默认"], summary="欢迎页")
def root():
    return {
        "message": "欢迎使用基础CRUD接口系统",
        "docs": "/docs",
        "redoc": "/redoc",
    }


# 注册路由
app.include_router(users.router)
app.include_router(articles.router)
