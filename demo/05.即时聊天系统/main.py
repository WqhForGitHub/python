"""FastAPI 应用入口。

启动方式：
    uvicorn main:app --reload

即时聊天系统 Demo：
- WebSocket 实时聊天
- 在线状态管理
- 群聊 / 私聊
- 消息历史
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from routers import chat, rooms

app = FastAPI(
    title="即时聊天系统",
    description=(
        "基于 FastAPI WebSocket 的即时聊天系统 Demo。\n\n"
        "## 功能特性\n"
        "- **WebSocket 实时通信**：`ws://host/ws/chat?user_id=N`\n"
        "- **在线状态**：用户上下线广播，`/rooms/online` 查询在线列表\n"
        "- **群聊**：加入房间后广播给房间内所有成员\n"
        "- **私聊**：点对点投递，不在线时返回 `delivered:false`\n"
        "- **消息历史**：进程内定长队列保存最近消息\n\n"
        "## 快速体验\n"
        "用两个浏览器标签页打开 `/static/index.html`，分别填不同 user_id 即可对话。"
    ),
    version="1.0.0",
)


@app.get("/", tags=["默认"], summary="欢迎页")
def root():
    return {
        "message": "欢迎使用即时聊天系统",
        "docs": "/docs",
        "websocket": "/ws/chat?user_id=1",
        "chat_client": "/static/index.html",
    }


app.include_router(rooms.router)
app.include_router(chat.router)

# 挂载静态文件（聊天客户端页面）
_static_dir = Path(__file__).resolve().parent / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")
