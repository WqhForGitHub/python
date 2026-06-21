# PyRedis —— Python 实现的简化版 Redis

纯标准库（`socket` + `selectors` + `threading`），支持 RESP 协议，**和真正的 redis-cli 互通**。

## 已实现

- **RESP 协议**：`+SimpleString`、`-Error`、`:Integer`、`$BulkString`、`*Array` 全部支持
- **事件循环**：`selectors` 单线程多路复用 + 异步出站缓冲
- **多 DB**：`SELECT 0..15`
- **数据类型**：String / List / Hash / Set / Sorted Set
- **过期**：`EXPIRE` / `PEXPIRE` / `TTL` / `PTTL` / `PERSIST`，惰性 + 后台线程随机扫描
- **持久化**：AOF（每次写命令以 RESP 格式追加），重启时回放

### 命令集

```
连接   : PING ECHO SELECT QUIT
通用   : KEYS EXISTS DEL TYPE FLUSHALL FLUSHDB DBSIZE INFO COMMAND
String : GET SET(NX/XX/EX/PX) INCR DECR INCRBY APPEND STRLEN MGET MSET
过期   : EXPIRE PEXPIRE TTL PTTL PERSIST
List   : LPUSH RPUSH LPOP RPOP LLEN LRANGE LINDEX
Hash   : HSET HGET HGETALL HDEL HKEYS HVALS HLEN HEXISTS
Set    : SADD SREM SISMEMBER SMEMBERS SCARD SINTER SUNION
ZSet   : ZADD ZRANGE ZSCORE ZREM ZCARD ZRANGEBYSCORE
```

## 用法

```bash
# 启动 server
python pyredis.py server --host=127.0.0.1 --port=6390 --aof=dump.aof

# 用本项目的 mini CLI
python pyredis.py cli --port=6390

# 用真正的 redis-cli（如果你装了）
redis-cli -p 6390

# 一键 demo（同进程同时跑 server + 客户端）
python pyredis.py demo
```

## CLI 示例

```
127.0.0.1:6390> SET name alice
OK
127.0.0.1:6390> GET name
alice
127.0.0.1:6390> ZADD score 10 tom 20 jerry 5 spike
(integer) 3
127.0.0.1:6390> ZRANGE score 0 -1
1) spike
2) tom
3) jerry
```

## 设计要点

- 解析器是状态保留的，按 byte 喂入即可，支持 TCP 任意切片
- `SortedSet` 简化实现：`dict` 存 member→score、`bisect` 维持有序对
- 过期：读取时检查过期 + 后台线程每 100ms 随机抽样 20 个 key 清理
- AOF：写命令以 RESP 数组形式追加；启动时按 RESP 解析并重放
