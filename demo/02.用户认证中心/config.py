"""应用配置。

所有配置项均支持通过环境变量覆盖默认值，便于在不同环境部署。
生产环境务必通过环境变量设置强随机的 SECRET_KEY。
"""

import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent

# ============================================================
# 数据库
# ============================================================
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./auth_demo.db")

# ============================================================
# JWT
# ============================================================
# 生产环境务必通过环境变量设置强随机密钥（建议 >= 32 字节）
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "dev-secret-key-please-change-me-in-production-with-a-long-random-string",
)
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Token 有效期（秒）
ACCESS_TOKEN_EXPIRE_SECONDS = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_SECONDS", "1800")
)  # 30 分钟
REFRESH_TOKEN_EXPIRE_SECONDS = int(
    os.getenv("REFRESH_TOKEN_EXPIRE_SECONDS", "604800")
)  # 7 天

# ============================================================
# 初始管理员（首次启动自动创建）
# ============================================================
INITIAL_ADMIN_USERNAME = os.getenv("INITIAL_ADMIN_USERNAME", "admin")
INITIAL_ADMIN_PASSWORD = os.getenv("INITIAL_ADMIN_PASSWORD", "Admin123456")
INITIAL_ADMIN_EMAIL = os.getenv("INITIAL_ADMIN_EMAIL", "admin@example.com")

# 注册新用户默认分配的角色名
DEFAULT_ROLE_NAME = os.getenv("DEFAULT_ROLE_NAME", "user")
