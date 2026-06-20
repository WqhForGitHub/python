"""auth-service 配置。"""
import os

SERVICE_NAME = "auth-service"
SERVICE_HOST = os.getenv("SERVICE_HOST", "127.0.0.1")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8001"))

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://127.0.0.1:8000")

# JWT
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "microservice-demo-secret-key-change-in-production",
)
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_SECONDS = int(os.getenv("ACCESS_TOKEN_EXPIRE_SECONDS", "3600"))

# user-service 地址（也可经网关发现，这里演示直接配置 + 网关兜底）
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://127.0.0.1:8002")
