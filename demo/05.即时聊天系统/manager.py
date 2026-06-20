"""WebSocket 连接管理器。

负责：
- 维护 user_id -> WebSocket 映射（在线状态）
- 维护 room -> set(user_id) 映射（群聊房间）
- 私聊 / 群聊消息分发
- 加入 / 离开房间
"""
import json
from datetime import datetime
from typing import Any

from fastapi import WebSocket

import store


class ConnectionManager:
    def __init__(self) -> None:
        # user_id -> WebSocket
        self.active: dict[int, WebSocket] = {}
        # room_name -> set(user_id)
        self.rooms: dict[str, set[int]] = {}

    # ------------------------------------------------------------
    # 在线状态
    # ------------------------------------------------------------
    def is_online(self, user_id: int) -> bool:
        return user_id in self.active

    def online_users(self) -> list[int]:
        return sorted(self.active.keys())

    # ------------------------------------------------------------
    # 房间
    # ------------------------------------------------------------
    def join_room(self, user_id: int, room: str) -> None:
        self.rooms.setdefault(room, set()).add(user_id)

    def leave_room(self, user_id: int, room: str) -> None:
        if room in self.rooms:
            self.rooms[room].discard(user_id)
            if not self.rooms[room]:
                del self.rooms[room]

    def room_members(self, room: str) -> list[int]:
        return sorted(self.rooms.get(room, set()))

    def list_rooms(self) -> list[str]:
        # 包含有消息历史但当前无人在线的房间
        rooms = set(self.rooms.keys()) | set(store.list_rooms())
        return sorted(rooms)

    # ------------------------------------------------------------
    # 连接生命周期
    # ------------------------------------------------------------
    async def connect(self, user_id: int, ws: WebSocket) -> None:
        await ws.accept()
        # 同一用户重复登录时踢掉旧连接
        if user_id in self.active:
            old = self.active.pop(user_id)
            try:
                await old.close(code=4001, reason="账号在其他设备登录")
            except Exception:  # noqa: BLE001
                pass
        self.active[user_id] = ws
        await self._broadcast_system(f"用户 {user_id} 上线")

    async def disconnect(self, user_id: int) -> None:
        self.active.pop(user_id, None)
        # 离开所有房间
        for room in list(self.rooms.keys()):
            self.leave_room(user_id, room)
        await self._broadcast_system(f"用户 {user_id} 下线")

    # ------------------------------------------------------------
    # 消息发送
    # ------------------------------------------------------------
    async def send_personal(self, user_id: int, data: dict[str, Any]) -> bool:
        """向指定用户发送，返回是否投递成功（在线）。"""
        ws = self.active.get(user_id)
        if ws is None:
            return False
        try:
            await ws.send_text(json.dumps(data, ensure_ascii=False))
            return True
        except Exception:  # noqa: BLE001
            await self.disconnect(user_id)
            return False

    async def broadcast_room(self, room: str, data: dict[str, Any]) -> None:
        """向房间内所有在线成员广播。"""
        for uid in list(self.rooms.get(room, set())):
            await self.send_personal(uid, data)

    async def _broadcast_system(self, content: str) -> None:
        ts = datetime.utcnow().isoformat() + "Z"
        data = {
            "type": "system",
            "room": "global",
            "from": 0,
            "content": content,
            "timestamp": ts,
        }
        for uid in list(self.active.keys()):
            await self.send_personal(uid, data)

    # ------------------------------------------------------------
    # 业务：私聊 / 群聊
    # ------------------------------------------------------------
    @staticmethod
    def dm_room(u1: int, u2: int) -> str:
        """私聊房间名（保证两人固定）。"""
        a, b = sorted((u1, u2))
        return f"dm:{a}_{b}"

    async def send_private(self, from_user: int, to_user: int, content: str) -> dict[str, Any]:
        """私聊：投递给接收者，并把发送者自己也回显一份。"""
        room = self.dm_room(from_user, to_user)
        ts = datetime.utcnow().isoformat() + "Z"
        data = {
            "type": "chat",
            "room": room,
            "from": from_user,
            "to": to_user,
            "content": content,
            "timestamp": ts,
        }
        store.record_message(room, from_user, to_user, content, ts)
        # 发给接收者
        delivered = await self.send_personal(to_user, data)
        # 回显给发送者（附投递状态）
        echo = {**data, "delivered": delivered}
        await self.send_personal(from_user, echo)
        return echo

    async def send_group(self, from_user: int, room: str, content: str) -> dict[str, Any]:
        """群聊：广播给房间内所有人（含发送者）。"""
        if from_user not in self.rooms.get(room, set()):
            # 自动加入房间
            self.join_room(from_user, room)
        ts = datetime.utcnow().isoformat() + "Z"
        data = {
            "type": "chat",
            "room": room,
            "from": from_user,
            "to": None,
            "content": content,
            "timestamp": ts,
        }
        store.record_message(room, from_user, None, content, ts)
        await self.broadcast_room(room, data)
        return data


# 全局单例
manager = ConnectionManager()
