"""FastAPI 应用入口。

启动方式：
    uvicorn main:app --reload

AI 接口服务系统 Demo：
- LLM 接口封装（mock / openai）
- 异步任务队列（asyncio worker）
- 请求限流（令牌桶）
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

import config
import models
import queue
from database import engine
from routers import chat, tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动后台 worker，关闭时清理。"""
    models.Base.metadata.create_all(bind=engine)
    await queue.task_queue.start()
    yield
    await queue.task_queue.stop()


app = FastAPI(
    title="AI接口服务系统",
    description=(
        "基于 FastAPI 的 AI 接口服务中台 Demo。\n\n"
        "## 功能特性\n"
        "- **LLM 接口封装**：mock（默认）/ openai，统一接口可切换\n"
        "- **同步聊天**：`/chat/completions` 实时返回\n"
        "- **异步任务队列**：`/tasks` 提交后异步处理，支持重试\n"
        "- **请求限流**：令牌桶算法，按用户隔离，超出返回 429\n\n"
        f"## 当前 LLM Provider\n`{config.LLM_PROVIDER}`\n\n"
        "## 用户标识\n通过请求头 `X-User-Id` 标识用户。"
    ),
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", tags=["默认"], summary="欢迎页")
def root():
    return {
        "message": "欢迎使用AI接口服务系统",
        "docs": "/docs",
        "llm_provider": config.LLM_PROVIDER,
        "queue_workers": config.TASK_QUEUE_WORKERS,
    }


app.include_router(chat.router)
app.include_router(tasks.router)
