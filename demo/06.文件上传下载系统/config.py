"""应用配置。"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# ============================================================
# 数据库
# ============================================================
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./files_demo.db")

# ============================================================
# 存储后端
# ============================================================
# local | minio
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")

# 本地存储目录
LOCAL_STORAGE_DIR = BASE_DIR / "uploads"
LOCAL_STORAGE_DIR.mkdir(exist_ok=True)

# MinIO 配置（仅当 STORAGE_BACKEND=minio 时生效）
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "demo-files")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

# ============================================================
# 上传限制
# ============================================================
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", str(10 * 1024 * 1024)))  # 10MB
ALLOWED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp",  # 图片
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",  # 文档
    ".txt", ".md", ".csv", ".zip",
}
