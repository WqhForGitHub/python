"""FastAPI 应用入口。

启动方式：
    uvicorn main:app --reload
"""
from fastapi import FastAPI

import models
from database import engine
from initial_data import init_db
from routers import auth, demo, permissions, roles, users

# 启动时自动建表 + 初始化默认数据（开发环境使用，生产环境推荐 Alembic 迁移）
models.Base.metadata.create_all(bind=engine)
init_db()

app = FastAPI(
    title="用户认证中心",
    description=(
        "基于 FastAPI 的用户认证中心 Demo。\n\n"
        "## 功能特性\n"
        "- **JWT 登录 / 注册**：基于 access_token 鉴权\n"
        "- **Refresh Token**：令牌轮转与吊销，支持登出\n"
        "- **RBAC 权限控制**：用户 - 角色 - 权限三级模型\n\n"
        "## 默认账号\n"
        "| 用户名 | 密码 | 角色 |\n"
        "| --- | --- | --- |\n"
        "| admin | Admin123456 | 超级管理员（全部权限） |\n"
        "| alice | Alice123456 | 普通用户（仅 article 权限） |"
    ),
    version="1.0.0",
)


@app.get("/", tags=["默认"], summary="欢迎页")
def root():
    return {
        "message": "欢迎使用用户认证中心",
        "docs": "/docs",
        "redoc": "/redoc",
    }


# 注册路由
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(roles.router)
app.include_router(permissions.router)
app.include_router(demo.router)
