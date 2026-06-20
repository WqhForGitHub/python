"""user-service 配置。"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SERVICE_NAME = "user-service"
SERVICE_HOST = os.getenv("SERVICE_HOST", "127.0.0.1")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8002"))

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://127.0.0.1:8000")

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./user_service.db")
