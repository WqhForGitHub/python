"""api-gateway 配置。"""
import os

GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", "8000"))
# 注册表心跳 TTL（秒），超时视为下线
HEARTBEAT_TTL = float(os.getenv("HEARTBEAT_TTL", "15"))
