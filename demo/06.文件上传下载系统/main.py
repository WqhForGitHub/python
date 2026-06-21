"""FastAPI 应用入口。

启动方式：
    uvicorn main:app --reload

文件上传下载系统 Demo：
- 图片 / 文档上传
- 本地存储 / MinIO 对象存储（可切换）
- 文件权限控制（public / private / shared）
"""

from fastapi import FastAPI

import models
import storage
from database import engine, SessionLocal
from routers import files

models.Base.metadata.create_all(bind=engine)
_seed()


def _seed() -> None:
    """写入示例用户（幂等）。"""
    db = SessionLocal()
    try:
        if db.query(models.User).count() == 0:
            db.add_all([models.User(username="alice"), models.User(username="bob")])
            db.commit()
    finally:
        db.close()


app = FastAPI(
    title="文件上传下载系统",
    description=(
        "基于 FastAPI 的文件上传下载系统 Demo。\n\n"
        "## 功能特性\n"
        "- **文件上传 / 下载**：支持图片、文档等\n"
        "- **存储后端可切换**：本地文件系统 / MinIO（S3 兼容）\n"
        "- **权限控制**：public / private / shared 三级可见性\n"
        "- **共享授权**：owner 可将文件共享给指定用户\n"
        "- **安全防护**：扩展名白名单、大小限制、目录穿越防护\n\n"
        f"## 当前存储后端\n`{storage.storage.backend_name}`\n\n"
        "## 用户标识\n通过请求头 `X-User-Id` 标识用户（预置：1=alice, 2=bob）。"
    ),
    version="1.0.0",
)


@app.get("/", tags=["默认"], summary="欢迎页")
def root():
    return {
        "message": "欢迎使用文件上传下载系统",
        "docs": "/docs",
        "storage_backend": storage.storage.backend_name,
    }


app.include_router(files.router)
