# -*- coding: utf-8 -*-
"""
简易缓存系统（LRU）
- 自实现 LRU 缓存（双向链表 + 字典）
- 支持容量上限、过期时间（TTL）、命中统计
- 提供 @lru_decorator 函数装饰器
- 线程安全
"""
import threading
import time
from typing import Any, Callable, Hashable, Optional


class _Node:
    __slots__ = ("key", "value", "expire_at", "prev", "next")

    def __init__(self, key, value, expire_at=None):
        self.key = key
        self.value = value
        self.expire_at = expire_at
        self.prev = None
        self.next = None


class LRUCache:
    def __init__(self, capacity: int = 128, ttl: Optional[float] = None):
        if capacity <= 0:
            raise ValueError("capacity 必须大于 0")
        self.capacity = capacity
        self.ttl = ttl
        self._lock = threading.RLock()
        self._map = {}
        # 哨兵节点
        self._head = _Node(None, None)  # 最近使用
        self._tail = _Node(None, None)  # 最久未使用
        self._head.next = self._tail
        self._tail.prev = self._head

        self.hits = 0
        self.misses = 0

    # ---- 链表操作 ----
    def _add_front(self, node: _Node):
        node.prev = self._head
        node.next = self._head.next
        self._head.next.prev = node
        self._head.next = node

    def _remove(self, node: _Node):
        node.prev.next = node.next
        node.next.prev = node.prev
        node.prev = node.next = None

    def _move_front(self, node: _Node):
        self._remove(node)
        self._add_front(node)

    # ---- 公共 API ----
    def get(self, key: Hashable, default=None):
        with self._lock:
            node = self._map.get(key)
            if node is None:
                self.misses += 1
                return default
            if node.expire_at is not None and node.expire_at < time.time():
                # 过期清理
                self._remove(node)
                self._map.pop(key, None)
                self.misses += 1
                return default
            self._move_front(node)
            self.hits += 1
            return node.value

    def put(self, key: Hashable, value: Any, ttl: Optional[float] = None):
        with self._lock:
            expire_at = None
            t = ttl if ttl is not None else self.ttl
            if t is not None:
                expire_at = time.time() + t

            if key in self._map:
                node = self._map[key]
                node.value = value
                node.expire_at = expire_at
                self._move_front(node)
                return

            node = _Node(key, value, expire_at)
            self._map[key] = node
            self._add_front(node)

            if len(self._map) > self.capacity:
                # 淘汰末尾
                lru = self._tail.prev
                self._remove(lru)
                self._map.pop(lru.key, None)

    def delete(self, key):
        with self._lock:
            node = self._map.pop(key, None)
            if node:
                self._remove(node)

    def clear(self):
        with self._lock:
            self._map.clear()
            self._head.next = self._tail
            self._tail.prev = self._head
            self.hits = 0
            self.misses = 0

    def __contains__(self, key):
        return self.get(key, _SENTINEL) is not _SENTINEL

    def __len__(self):
        return len(self._map)

    def stats(self):
        total = self.hits + self.misses
        rate = (self.hits / total * 100) if total else 0.0
        return {"size": len(self._map), "capacity": self.capacity,
                "hits": self.hits, "misses": self.misses,
                "hit_rate": f"{rate:.1f}%"}

    def keys(self):
        with self._lock:
            # 按 LRU 顺序：从最新到最老
            keys = []
            n = self._head.next
            while n is not self._tail:
                keys.append(n.key)
                n = n.next
            return keys


_SENTINEL = object()


def lru_decorator(capacity=128, ttl=None):
    """函数装饰器：基于参数缓存返回值"""
    cache = LRUCache(capacity=capacity, ttl=ttl)

    def deco(fn: Callable):
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            v = cache.get(key, _SENTINEL)
            if v is not _SENTINEL:
                return v
            r = fn(*args, **kwargs)
            cache.put(key, r)
            return r
        wrapper.cache = cache
        wrapper.cache_info = cache.stats
        wrapper.cache_clear = cache.clear
        return wrapper
    return deco


# ---------- demo ----------
def _demo():
    print("== LRU 基本演示 ==")
    c = LRUCache(capacity=3)
    c.put("a", 1); c.put("b", 2); c.put("c", 3)
    print("keys:", c.keys())
    c.get("a")
    c.put("d", 4)  # 淘汰 b
    print("after access a, put d:", c.keys())  # [d, a, c]
    print("stats:", c.stats())

    print("\n== TTL 演示 ==")
    c2 = LRUCache(capacity=10, ttl=0.5)
    c2.put("x", "hello")
    print("立即取:", c2.get("x"))
    time.sleep(0.6)
    print("0.6s 后:", c2.get("x"))

    print("\n== 装饰器演示 ==")

    @lru_decorator(capacity=64)
    def slow_fib(n):
        if n < 2:
            return n
        return slow_fib(n - 1) + slow_fib(n - 2)

    t = time.time()
    print("fib(30) =", slow_fib(30))
    print(f"耗时 {time.time()-t:.3f}s, 缓存信息: {slow_fib.cache_info()}")


if __name__ == "__main__":
    _demo()
