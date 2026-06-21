# PyMQ —— 类 RabbitMQ 简版消息队列

纯 Python 标准库 + TCP 实现的迷你消息队列服务。

## 已实现的 AMQP-like 概念

| 概念 | 说明 |
|------|------|
| Exchange | 三种类型：`direct` / `fanout` / `topic`（`*` 一段、`#` 多段） |
| Queue    | 内存队列，可选持久化 |
| Binding  | `(exchange, queue, routing_key)` 三元组 |
| publish / consume | 同步发布、回调式消费 |
| ack / nack | 显式确认；nack 默认重新入队 |
| 自动 requeue | 消费者断线时未 ack 的消息重新入队 |
| 持久化 | 开启时把声明 / 发布操作写入 jsonl，重启回放 |

## 协议

最小化的二进制帧格式：

```
[4字节大端长度][JSON-UTF8 body]
```

每个连接一个线程，broker 通过 connection 对象推送 `deliver` 帧。

## 用法

```bash
# 1) 启动 broker
python pymq.py broker --host=127.0.0.1 --port=5673 [--persist=mq.jsonl]

# 2) 在另一个终端发布
python pymq.py publish ex topic order.created '{"id":1}'

# 3) 在又一个终端消费
python pymq.py consume orders --bind=ex:order.*

# 0) 一键 demo（在同一进程内启动 broker / producer / consumer）
python pymq.py demo
```

## 编程接口

```python
from pymq import BlockingClient

c = BlockingClient(host="127.0.0.1", port=5673)
c.connect()
c.declare_exchange("ex", "topic")
c.declare_queue("orders")
c.bind("ex", "orders", "order.*")

def on_msg(msg, delivery_tag, queue):
    print("got", msg)
    return True   # True -> ack, False -> nack(requeue)

c.consume("orders", on_msg)
c.publish("ex", "order.created", {"id": 1})
```

## 设计要点

- broker 单进程多线程，connection / dispatch 都串行加锁
- 路由：`fanout` 广播；`direct` 精确匹配；`topic` 支持 `*`/`#`
- 默认 exchange `""`：`routing_key` 当作队列名直投（兼容 AMQP 传统）
- 消费者多于一个时按 round-robin 派发
