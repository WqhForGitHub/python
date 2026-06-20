"""应用配置。"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# ============================================================
# 数据库
# ============================================================
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ai_demo.db")

# ============================================================
# LLM 配置
# ============================================================
# mock | openai
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
# 单次请求最大 token
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1024"))
# 模拟请求耗时（秒，仅 mock 模式）
MOCK_LATENCY = float(os.getenv("MOCK_LATENCY", "1.5"))

# ============================================================
# 限流（令牌桶）
# ============================================================
RATE_LIMIT_CAPACITY = int(os.getenv("RATE_LIMIT_CAPACITY", "5"))   # 桶容量
RATE_LIMIT_REFILL = int(os.getenv("RATE_LIMIT_REFILL", "5"))       # 每秒补充令牌数

# ============================================================
# 任务队列
# ============================================================
TASK_QUEUE_WORKERS = int(os.getenv("TASK_QUEUE_WORKERS", "2"))     # 后台 worker 数
TASK_MAX_RETRIES = int(os.getenv("TASK_MAX_RETRIES", "2"))
