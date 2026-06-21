"""房间 / 在线状态相关 HTTP 接口。"""

from fastapi import APIRouter

import manager
import store
import schemas

router = APIRouter(prefix="/rooms", tags=["房间与在线状态"])


@router.get("/online", summary="在线用户列表")
def online_users():
    return {"online": manager.online_users(), "count": len(manager.online_users())}


@router.get("/", summary="所有房间列表")
def list_rooms():
    return {"rooms": manager.list_rooms()}


@router.get("/{room}/members", summary="房间在线成员")
def room_members(room: str):
    return {"room": room, "members": manager.room_members(room)}


@router.get("/{room}/history", summary="房间消息历史")
def room_history(room: str, limit: int = 50):
    items = store.get_history(room, limit=limit)
    return {"room": room, "count": len(items), "items": items}


@router.get("/dm/{u1}/{u2}/history", summary="私聊会话历史")
def dm_history(u1: int, u2: int, limit: int = 50):
    room = manager.dm_room(u1, u2)
    items = store.get_history(room, limit=limit)
    return {"room": room, "count": len(items), "items": items}
