"""消息历史存储（进程内，Demo 用）。

每个 room 维护一个定长队列，仅保留最近 HISTORY_LIMIT 条。
生产环境应替换为 Redis List / 数据库。
"""
from collections import deque

import config
import schemas


# room -> deque[MessageRecord]
_history: dict[str, deque] = {}


def record_message(
    room: str, from_user: int, to: int | None, content: str, timestamp: str
) -> schemas.MessageRecord:
    rec = schemas.MessageRecord(
        room=room,
        from_user=from_user,
        to=to,
        content=content,
        timestamp=timestamp,
    )
    dq = _history.setdefault(room, deque(maxlen=config.HISTORY_LIMIT))
    dq.append(rec)
    return rec


def get_history(room: str, limit: int = 50) -> list[schemas.MessageRecord]:
    dq = _history.get(room, deque())
    items = list(dq)
    if limit and len(items) > limit:
        items = items[-limit:]
    return items


def list_rooms() -> list[str]:
    return list(_history.keys())
