"""存储后端抽象。

支持两种后端：
1. local：本地文件系统（默认，无需任何外部依赖）
2. minio ：MinIO / S3 兼容对象存储（需安装 minio 库并启动 MinIO 服务）

二者实现统一的 StorageBackend 接口：save / open / delete / exists。
"""
import shutil
from abc import ABC, abstractmethod
from pathlib import Path

import config


class StorageBackend(ABC):
    """存储后端统一接口。"""

    backend_name: str = "abstract"

    @abstractmethod
    def save(self, key: str, data: bytes) -> None: ...

    @abstractmethod
    def open(self, key: str) -> bytes: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...

    @abstractmethod
    def exists(self, key: str) -> bool: ...


# ============================================================
# 本地文件系统
# ============================================================
class LocalStorage(StorageBackend):
    backend_name = "local"

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # key 形如 "2026/06/abc.jpg"，防止目录穿越
        p = (self.base_dir / key).resolve()
        if not str(p).startswith(str(self.base_dir.resolve())):
            raise ValueError("非法的存储 key")
        return p

    def save(self, key: str, data: bytes) -> None:
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    def open(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        p = self._path(key)
        if p.exists():
            p.unlink()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()


# ============================================================
# MinIO / S3 兼容对象存储
# ============================================================
class MinIOStorage(StorageBackend):
    backend_name = "minio"

    def __init__(self) -> None:
        from minio import Minio  # type: ignore

        self.client = Minio(
            config.MINIO_ENDPOINT,
            access_key=config.MINIO_ACCESS_KEY,
            secret_key=config.MINIO_SECRET_KEY,
            secure=config.MINIO_SECURE,
        )
        self.bucket = config.MINIO_BUCKET
        # 自动创建 bucket
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    def save(self, key: str, data: bytes) -> None:
        from io import BytesIO

        self.client.put_object(
            self.bucket, key, BytesIO(data), length=len(data)
        )

    def open(self, key: str) -> bytes:
        resp = self.client.get_object(self.bucket, key)
        try:
            return resp.read()
        finally:
            resp.close()
            resp.release_conn()

    def delete(self, key: str) -> None:
        self.client.remove_object(self.bucket, key)

    def exists(self, key: str) -> bool:
        try:
            self.client.stat_object(self.bucket, key)
            return True
        except Exception:  # noqa: BLE001
            return False


# ============================================================
# 工厂：根据配置选择后端
# ============================================================
def get_storage() -> StorageBackend:
    if config.STORAGE_BACKEND == "minio":
        try:
            return MinIOStorage()
        except Exception as e:  # noqa: BLE001
            # MinIO 不可用时降级为本地存储，保证 Demo 可运行
            print(f"[storage] MinIO 不可用，降级为本地存储：{e}")
            return LocalStorage(config.LOCAL_STORAGE_DIR)
    return LocalStorage(config.LOCAL_STORAGE_DIR)


storage = get_storage()
