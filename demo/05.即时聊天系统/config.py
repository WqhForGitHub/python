"""应用配置。"""

import os

# 在线状态心跳间隔（秒）
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "30"))

# 消息历史保留条数（每个房间 / 每个私聊会话）
HISTORY_LIMIT = int(os.getenv("HISTORY_LIMIT", "100"))
