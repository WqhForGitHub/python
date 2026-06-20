"""WebSocket 聊天端点。

连接方式：
    ws://127.0.0.1:8000/ws/chat?user_id=1

消息格式见 schemas.WSMessage。
"""
import json
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

import manager
import schemas
import store

router = APIRouter(tags=["WebSocket 聊天"])


@router.websocket("/ws/chat")
async def chat_endpoint(ws: WebSocket, user_id: int = 1):
    """WebSocket 聊天端点。

    Query 参数：
        user_id: 用户 ID（Demo 简化，无鉴权）

    客户端发送的消息（JSON）：
        - {"type":"chat","room":"general","content":"hello"}      群聊
        - {"type":"chat","to":2,"content":"hi"}                   私聊
        - {"type":"join","room":"general"}                        加入房间
        - {"type":"leave","room":"general"}                       离开房间
        - {"type":"heartbeat"}                                    心跳

    服务端会回显 / 广播消息，并发送系统通知（上下线）。
    """
    await manager.connect(user_id, ws)
    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = schemas.WSMessage.model_validate_json(raw)
            except Exception as e:  # noqa: BLE001
                await manager.send_personal(
                    user_id,
                    {
                        "type": "system",
                        "room": "global",
                        "from": 0,
                        "content": f"消息格式错误：{e}",
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                    },
                )
                continue

            if msg.type == "heartbeat":
                await manager.send_personal(
                    user_id,
                    {
                        "type": "heartbeat",
                        "room": "global",
                        "from": 0,
                        "content": "pong",
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                    },
                )

            elif msg.type == "join":
                room = msg.room or "general"
                manager.join_room(user_id, room)
                ts = datetime.utcnow().isoformat() + "Z"
                data = {
                    "type": "join",
                    "room": room,
                    "from": user_id,
                    "content": f"用户 {user_id} 加入房间 {room}",
                    "timestamp": ts,
                }
                await manager.broadcast_room(room, data)

            elif msg.type == "leave":
                room = msg.room or "general"
                ts = datetime.utcnow().isoformat() + "Z"
                data = {
                    "type": "leave",
                    "room": room,
                    "from": user_id,
                    "content": f"用户 {user_id} 离开房间 {room}",
                    "timestamp": ts,
                }
                await manager.broadcast_room(room, data)
                manager.leave_room(user_id, room)

            elif msg.type == "chat":
                if msg.to is not None:
                    # 私聊
                    await manager.send_private(user_id, msg.to, msg.content)
                elif msg.room:
                    # 群聊
                    await manager.send_group(user_id, msg.room, msg.content)
                else:
                    await manager.send_personal(
                        user_id,
                        {
                            "type": "system",
                            "room": "global",
                            "from": 0,
                            "content": "请指定 room（群聊）或 to（私聊）",
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                        },
                    )

    except WebSocketDisconnect:
        await manager.disconnect(user_id)
    except Exception:  # noqa: BLE001
        await manager.disconnect(user_id)
