"""应用配置。"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./logs_demo.db")

# 慢请求阈值（秒），超过则打 WARN 日志
SLOW_REQUEST_THRESHOLD = float(os.getenv("SLOW_REQUEST_THRESHOLD", "1.0"))

# 请求 ID 请求头名
REQUEST_ID_HEADER = "X-Request-ID"
