"""Redis 缓存客户端 + 兜底的内存缓存。

为便于无 Redis 环境运行 Demo，启动时若连不上 Redis，则自动降级为
进程内字典缓存（功能一致，但不具备分布式能力）。
"""

import json
import threading
import time
from typing import Any

import redis

import config

# ------------------------------------------------------------
# 尝试连接 Redis；失败则降级为内存缓存
# ------------------------------------------------------------
_redis_client: "redis.Redis | None" = None
try:
    _redis_client = redis.from_url(config.REDIS_URL, decode_responses=True)
    _redis_client.ping()
except Exception:  # noqa: BLE001  任意连接失败均降级
    _redis_client = None


class _MemoryCache:
    """进程内字典缓存，模拟 Redis 字符串接口（仅用于 Demo 降级）。"""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}
        self._expiry: dict[str, float] = {}
        self._lock = threading.Lock()

    def _purge(self, key: str) -> None:
        exp = self._expiry.get(key)
        if exp is not None and exp < time.time():
            self._store.pop(key, None)
            self._expiry.pop(key, None)

    def get(self, key: str) -> str | None:
        with self._lock:
            self._purge(key)
            return self._store.get(key)

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        with self._lock:
            self._store[key] = value
            if ex:
                self._expiry[key] = time.time() + ex
            else:
                self._expiry.pop(key, None)

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)
            self._expiry.pop(key, None)

    def keys(self, pattern: str) -> list[str]:
        # 简单实现：仅支持 * 通配
        import fnmatch

        with self._lock:
            for k in list(self._store.keys()):
                self._purge(k)
            return [k for k in self._store.keys() if fnmatch.fnmatch(k, pattern)]


_mem_cache = _MemoryCache()


def is_redis_available() -> bool:
    return _redis_client is not None


# ------------------------------------------------------------
# 高层缓存 API
# ------------------------------------------------------------
def cache_get_json(key: str) -> Any | None:
    raw = _redis_client.get(key) if _redis_client else _mem_cache.get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


def cache_set_json(key: str, value: Any, ttl: int | None = None) -> None:
    raw = json.dumps(value, ensure_ascii=False, default=str)
    if _redis_client:
        _redis_client.set(key, raw, ex=ttl)
    else:
        _mem_cache.set(key, raw, ex=ttl)


def cache_delete(key: str) -> None:
    if _redis_client:
        _redis_client.delete(key)
    else:
        _mem_cache.delete(key)


def cache_keys(pattern: str) -> list[str]:
    if _redis_client:
        return _redis_client.keys(pattern)
    return _mem_cache.keys(pattern)


# 购物车使用 Hash 结构存储（user_id -> {product_id: quantity}）
def cart_get_all(user_id: int) -> dict[str, int]:
    """返回 {product_id(str): quantity(int)}。"""
    if _redis_client:
        raw = _redis_client.hgetall(f"cart:{user_id}")
        return {k: int(v) for k, v in raw.items()}
    data = cache_get_json(f"cart:{user_id}")
    if data is None:
        return {}
    return {k: int(v) for k, v in data.items()}


def cart_set_item(user_id: int, product_id: int, quantity: int) -> None:
    if _redis_client:
        _redis_client.hset(f"cart:{user_id}", str(product_id), quantity)
        _redis_client.expire(f"cart:{user_id}", config.CART_TTL)
    else:
        cart = cart_get_all(user_id)
        cart[str(product_id)] = quantity
        cache_set_json(f"cart:{user_id}", cart, ttl=config.CART_TTL)


def cart_remove_item(user_id: int, product_id: int) -> None:
    if _redis_client:
        _redis_client.hdel(f"cart:{user_id}", str(product_id))
    else:
        cart = cart_get_all(user_id)
        cart.pop(str(product_id), None)
        cache_set_json(f"cart:{user_id}", cart, ttl=config.CART_TTL)


def cart_clear(user_id: int) -> None:
    if _redis_client:
        _redis_client.delete(f"cart:{user_id}")
    else:
        cache_delete(f"cart:{user_id}")
