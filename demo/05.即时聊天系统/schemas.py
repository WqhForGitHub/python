"""Pydantic 模型。

WebSocket 消息采用统一信封：
{
  "type": "chat" | "join" | "leave" | "system" | "heartbeat" | "history",
  "room": str,        # 房间名；私聊用 "dm:{min_uid}_{max_uid}"
  "from": int,        # 发送者 user_id（系统消息为 0）
  "to": int | null,   # 私聊接收者；群聊为 null
  "content": str,
  "timestamp": str
}
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class WSMessage(BaseModel):
    """WebSocket 客户端 -> 服务端的消息。"""

    type: Literal["chat", "join", "leave", "heartbeat"] = Field(
        ..., description="消息类型"
    )
    room: str | None = Field(None, description="目标房间（群聊）")
    to: int | None = Field(None, description="私聊接收者 user_id")
    content: str = Field("", description="消息内容")


class BroadcastMessage(BaseModel):
    """服务端 -> 客户端的消息（含元数据）。"""

    type: Literal["chat", "join", "leave", "system", "history"]
    room: str
    from_user: int = Field(0, alias="from")
    to: int | None = None
    content: str = ""
    timestamp: str

    model_config = {"populate_by_name": True}


class RoomInfo(BaseModel):
    name: str
    members: list[int]
    online: list[int]


class MessageRecord(BaseModel):
    room: str
    from_user: int
    to: int | None
    content: str
    timestamp: str
