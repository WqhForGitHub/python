"""应用配置。"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# ============================================================
# 数据库
# ============================================================
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./shop_demo.db")

# ============================================================
# Redis
# ============================================================
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
# 购物车缓存 TTL（秒），0 表示不过期
CART_TTL = int(os.getenv("CART_TTL", "604800"))  # 7 天
# 商品详情缓存 TTL
PRODUCT_CACHE_TTL = int(os.getenv("PRODUCT_CACHE_TTL", "300"))  # 5 分钟
