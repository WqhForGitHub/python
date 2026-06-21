"""应用配置。

所有配置项均支持通过环境变量覆盖默认值，便于在不同环境部署。
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# ============================================================
# 异步数据库（aiosqlite）
# ============================================================
# 注意：异步驱动需使用 sqlite+aiosqlite 协议
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", "sqlite+aiosqlite:///./blog_demo.db"
)

# ============================================================
# 分页
# ============================================================
DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", "10"))
MAX_PAGE_SIZE = int(os.getenv("MAX_PAGE_SIZE", "100"))
