# 65. Key-Value 存储系统

类 Redis 的 Key-Value 数据库（仅 Python 标准库）。

## 特性
- AOF 追加日志 + 快照 (SAVE) 双重持久化
- TTL 过期、KEYS / TYPE / EXISTS
- 数据类型：string / list / hash
- TCP 文本协议 + 多线程并发

## 命令
```
SET key value      GET key      DEL key
EXISTS key         KEYS         TYPE key
EXPIRE key sec     TTL key      PERSIST key
LPUSH key v ..     RPUSH key v..      LRANGE key start stop
HSET key f v       HGET key f   HGETALL key   HDEL key f
DBSIZE  FLUSHALL  SAVE  PING  HELP  QUIT
```

## 用法
```
# 服务端
python kvstore.py serve --host 127.0.0.1 --port 6380 --dir kvdata

# 客户端
python kvstore.py cli --host 127.0.0.1 --port 6380

# 本地嵌入式 REPL
python kvstore.py local
```

示例：
```
> SET name Tom
OK
> GET name
Tom
> EXPIRE name 60
1
> TTL name
59
> LPUSH list a b c
3
> LRANGE list 0 -1
c, b, a
> HSET user:1 name Alice
OK
> HGETALL user:1
name=Alice
> SAVE
OK saved 3 keys
```
