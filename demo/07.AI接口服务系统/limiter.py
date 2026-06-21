"""请求限流：令牌桶算法（进程内，按用户隔离）。

每个用户一个桶：
- capacity：桶最大容量
- refill：每秒补充的令牌数
请求时消耗 1 个令牌，不足则 429。
"""

import threading
import time

import config


class TokenBucket:
    def __init__(self, capacity: int, refill_per_sec: int) -> None:
        self.capacity = capacity
        self.refill = refill_per_sec
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()
        self._lock = threading.Lock()

    def consume(self, amount: float = 1.0) -> bool:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill)
            self.last_refill = now
            if self.tokens >= amount:
                self.tokens -= amount
                return True
            return False

    def available(self) -> float:
        """当前可用令牌数（仅用于展示）。"""
        now = time.monotonic()
        elapsed = now - self.last_refill
        return min(self.capacity, self.tokens + elapsed * self.refill)


class RateLimiter:
    """按 key（通常为 user_id）管理多个令牌桶。"""

    def __init__(self, capacity: int, refill_per_sec: int) -> None:
        self.capacity = capacity
        self.refill = refill_per_sec
        self._buckets: dict[str, TokenBucket] = {}
        self._lock = threading.Lock()

    def _get(self, key: str) -> TokenBucket:
        with self._lock:
            if key not in self._buckets:
                self._buckets[key] = TokenBucket(self.capacity, self.refill)
            return self._buckets[key]

    def allow(self, key: str) -> bool:
        return self._get(key).consume(1.0)

    def status(self, key: str) -> dict:
        bucket = self._get(key)
        return {
            "capacity": self.capacity,
            "refill_per_sec": self.refill,
            "available": round(bucket.available(), 2),
        }


# 全局单例
limiter = RateLimiter(config.RATE_LIMIT_CAPACITY, config.RATE_LIMIT_REFILL)
