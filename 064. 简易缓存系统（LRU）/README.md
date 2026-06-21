# 64. 简易缓存系统（LRU）

手写 LRU 缓存：双向链表 + 字典，支持 TTL 与命中率统计。

## API
```python
c = LRUCache(capacity=128, ttl=60)
c.put("k", "v")
c.get("k")
c.delete("k")
c.stats()    # {'hits':..,'misses':..,'hit_rate':..}
```

装饰器：
```python
@lru_decorator(capacity=64)
def fib(n): ...
fib.cache_info()
fib.cache_clear()
```

## 运行
```
python lru_cache.py
```
