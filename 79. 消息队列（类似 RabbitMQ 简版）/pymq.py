# -*- coding: utf-8 -*-
"""
PyMQ —— 类 RabbitMQ 简版消息队列（纯 Python 标准库 / TCP）

特性：
- 自定义二进制帧协议（length-prefixed JSON）
- AMQP-like 概念：
    Exchange (direct / fanout / topic)
    Queue
    Binding   (exchange + routing_key -> queue)
    publish / consume / ack / nack
- 多线程 broker：每连接一个线程；消费者推送消息
- 持久化（可选）：消息以 JSONL 形式落到磁盘，重启时回放
- 简单 ACK：未 ack 的消息在消费者断开时重新入队
- 客户端：BlockingClient（同步发布、消费回调）

用法：
    # 1) 启动 broker
    python pymq.py broker --host=127.0.0.1 --port=5673
    # 2) 在另一个终端发布
    python pymq.py publish my.exchange direct order.created '{"id":1}'
    # 3) 在又一个终端消费
    python pymq.py consume my.queue --bind=my.exchange:order.*

或直接：
    python pymq.py demo
内置 demo 会在同一进程内启动 broker、生产者、消费者。
"""
import os
import sys
import json
import time
import socket
import struct
import threading
import queue
from collections import defaultdict, deque
from typing import Callable, Optional, Dict, List


# ============================================================
# 帧编解码：4 字节大端长度 + JSON
# ============================================================
def send_frame(sock: socket.socket, obj: dict):
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    sock.sendall(struct.pack(">I", len(data)) + data)


def recv_frame(sock: socket.socket) -> Optional[dict]:
    head = _recv_exact(sock, 4)
    if head is None:
        return None
    (n,) = struct.unpack(">I", head)
    if n == 0 or n > 32 * 1024 * 1024:
        return None
    body = _recv_exact(sock, n)
    if body is None:
        return None
    try:
        return json.loads(body.decode("utf-8"))
    except Exception:
        return None


def _recv_exact(sock: socket.socket, n: int) -> Optional[bytes]:
    buf = b""
    while len(buf) < n:
        try:
            chunk = sock.recv(n - len(buf))
        except (ConnectionError, OSError):
            return None
        if not chunk:
            return None
        buf += chunk
    return buf


# ============================================================
# Broker
# ============================================================
class Queue_:
    def __init__(self, name, durable=False):
        self.name = name
        self.durable = durable
        self.messages: deque = deque()           # 待派发
        self.unacked: Dict[str, dict] = {}       # delivery_tag -> message
        self.consumers: List["Consumer"] = []
        self.rr_index = 0
        self.lock = threading.Lock()


class Exchange_:
    def __init__(self, name, kind="direct"):
        self.name = name
        self.kind = kind
        # bindings: list of (routing_key, queue_name)
        self.bindings: List = []


class Consumer:
    def __init__(self, conn, consumer_tag, queue_name, no_ack=False):
        self.conn = conn
        self.tag = consumer_tag
        self.queue = queue_name
        self.no_ack = no_ack


class Broker:
    def __init__(self, host="127.0.0.1", port=5673, persist_path=None):
        self.host = host
        self.port = port
        self.persist_path = persist_path
        self.exchanges: Dict[str, Exchange_] = {}
        self.queues: Dict[str, Queue_] = {}
        self.lock = threading.Lock()
        self._tag_seq = 0
        self._sock = None
        self._stop = False
        # 默认 direct exchange
        self.declare_exchange("", "direct")

    # -------- 持久化 --------
    def _persist_append(self, record):
        if not self.persist_path:
            return
        with open(self.persist_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _persist_replay(self):
        if not self.persist_path or not os.path.exists(self.persist_path):
            return
        with open(self.persist_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if rec["op"] == "exchange":
                    self.declare_exchange(rec["name"], rec["kind"])
                elif rec["op"] == "queue":
                    self.declare_queue(rec["name"], durable=rec.get("durable", False))
                elif rec["op"] == "bind":
                    self.bind(rec["exchange"], rec["queue"], rec["routing_key"])
                elif rec["op"] == "publish":
                    self._enqueue_message(rec["exchange"], rec["routing_key"], rec["message"], persist=False)
        print(f"[broker] replayed persisted state from {self.persist_path}")

    # -------- AMQP 模拟操作 --------
    def declare_exchange(self, name, kind="direct"):
        with self.lock:
            if name not in self.exchanges:
                self.exchanges[name] = Exchange_(name, kind)
                self._persist_append({"op": "exchange", "name": name, "kind": kind})

    def declare_queue(self, name, durable=False):
        with self.lock:
            if name not in self.queues:
                self.queues[name] = Queue_(name, durable=durable)
                self._persist_append({"op": "queue", "name": name, "durable": durable})

    def bind(self, exchange, queue_name, routing_key=""):
        with self.lock:
            ex = self.exchanges.get(exchange)
            if not ex:
                self.exchanges[exchange] = Exchange_(exchange, "direct")
                ex = self.exchanges[exchange]
            if queue_name not in self.queues:
                self.queues[queue_name] = Queue_(queue_name)
            ex.bindings.append((routing_key, queue_name))
            self._persist_append({
                "op": "bind", "exchange": exchange,
                "queue": queue_name, "routing_key": routing_key,
            })

    def publish(self, exchange, routing_key, message):
        return self._enqueue_message(exchange, routing_key, message, persist=True)

    def _enqueue_message(self, exchange, routing_key, message, persist=True):
        # 默认 exchange：把 routing_key 作为队列名直投
        if exchange == "":
            qname = routing_key
            self.declare_queue(qname)
            self._deliver_to_queue(qname, message)
            if persist:
                self._persist_append({"op": "publish", "exchange": "",
                                      "routing_key": routing_key, "message": message})
            return 1

        ex = self.exchanges.get(exchange)
        if ex is None:
            return 0
        delivered = 0
        target_queues = set()
        for rk, qn in ex.bindings:
            if ex.kind == "fanout":
                target_queues.add(qn)
            elif ex.kind == "direct":
                if rk == routing_key:
                    target_queues.add(qn)
            elif ex.kind == "topic":
                if _topic_match(rk, routing_key):
                    target_queues.add(qn)
        for qn in target_queues:
            self._deliver_to_queue(qn, message)
            delivered += 1
        if persist:
            self._persist_append({"op": "publish", "exchange": exchange,
                                  "routing_key": routing_key, "message": message})
        return delivered

    def _deliver_to_queue(self, qname, message):
        q = self.queues.get(qname)
        if q is None:
            return
        with q.lock:
            q.messages.append(message)
        self._dispatch(q)

    def _next_tag(self):
        with self.lock:
            self._tag_seq += 1
            return f"d{self._tag_seq}"

    def _dispatch(self, q: Queue_):
        """以 round-robin 把待派发消息发给 active consumers。"""
        with q.lock:
            if not q.consumers or not q.messages:
                return
            # 一次能派多少就派多少
            while q.messages and q.consumers:
                msg = q.messages.popleft()
                # 选一个还活着的 consumer
                tries = 0
                consumer = None
                while tries < len(q.consumers):
                    q.rr_index = (q.rr_index + 1) % len(q.consumers)
                    c = q.consumers[q.rr_index]
                    if not c.conn.alive:
                        continue
                    consumer = c
                    break
                if consumer is None:
                    q.messages.appendleft(msg)
                    return
                tag = self._next_tag()
                if not consumer.no_ack:
                    q.unacked[tag] = msg
                ok = consumer.conn.send({
                    "type": "deliver",
                    "queue": q.name,
                    "delivery_tag": tag,
                    "consumer_tag": consumer.tag,
                    "message": msg,
                })
                if not ok:
                    # 发送失败：放回队列、移除 consumer
                    if tag in q.unacked:
                        msg = q.unacked.pop(tag)
                    q.messages.appendleft(msg)
                    return

    def ack(self, queue_name, delivery_tag):
        q = self.queues.get(queue_name)
        if not q:
            return
        with q.lock:
            q.unacked.pop(delivery_tag, None)

    def nack(self, queue_name, delivery_tag, requeue=True):
        q = self.queues.get(queue_name)
        if not q:
            return
        with q.lock:
            msg = q.unacked.pop(delivery_tag, None)
            if msg is not None and requeue:
                q.messages.appendleft(msg)
        if msg is not None and requeue:
            self._dispatch(q)

    def attach_consumer(self, conn, consumer_tag, queue_name, no_ack=False):
        self.declare_queue(queue_name)
        q = self.queues[queue_name]
        c = Consumer(conn, consumer_tag, queue_name, no_ack=no_ack)
        with q.lock:
            q.consumers.append(c)
        self._dispatch(q)
        return c

    def detach_consumer(self, conn):
        # 把这个连接相关的所有 unacked 消息重新入队
        for q in list(self.queues.values()):
            with q.lock:
                q.consumers = [c for c in q.consumers if c.conn is not conn]
                # requeue unacked of this conn （不区分 tag 归属，简化处理：全部 requeue）
                if not q.consumers and q.unacked:
                    for tag, msg in list(q.unacked.items()):
                        q.messages.appendleft(msg)
                    q.unacked.clear()

    # -------- 网络层 --------
    def serve(self):
        self._persist_replay()
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self.host, self.port))
        self._sock.listen(64)
        print(f"[broker] listening on {self.host}:{self.port}")
        try:
            while not self._stop:
                try:
                    cs, addr = self._sock.accept()
                except OSError:
                    break
                conn = Connection(self, cs, addr)
                t = threading.Thread(target=conn.run, daemon=True)
                t.start()
        finally:
            self._sock.close()

    def stop(self):
        self._stop = True
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass


def _topic_match(pattern: str, routing_key: str) -> bool:
    """AMQP topic：'*' = 一段，'#' = 任意段。"""
    pp = pattern.split(".")
    rk = routing_key.split(".")
    return _topic_match_helper(pp, rk)


def _topic_match_helper(pp, rk):
    if not pp:
        return not rk
    if pp[0] == "#":
        if len(pp) == 1:
            return True
        for i in range(len(rk) + 1):
            if _topic_match_helper(pp[1:], rk[i:]):
                return True
        return False
    if not rk:
        return False
    if pp[0] == "*" or pp[0] == rk[0]:
        return _topic_match_helper(pp[1:], rk[1:])
    return False


# ============================================================
# Broker Connection（每客户端一个线程）
# ============================================================
class Connection:
    def __init__(self, broker: Broker, sock: socket.socket, addr):
        self.broker = broker
        self.sock = sock
        self.addr = addr
        self.alive = True
        self.send_lock = threading.Lock()

    def send(self, obj) -> bool:
        if not self.alive:
            return False
        try:
            with self.send_lock:
                send_frame(self.sock, obj)
            return True
        except Exception:
            self.alive = False
            return False

    def run(self):
        try:
            while self.alive:
                msg = recv_frame(self.sock)
                if msg is None:
                    break
                self._handle(msg)
        finally:
            self.alive = False
            self.broker.detach_consumer(self)
            try:
                self.sock.close()
            except Exception:
                pass

    def _handle(self, msg):
        op = msg.get("op")
        if op == "declare_exchange":
            self.broker.declare_exchange(msg["name"], msg.get("kind", "direct"))
            self.send({"type": "ok"})
        elif op == "declare_queue":
            self.broker.declare_queue(msg["name"], durable=msg.get("durable", False))
            self.send({"type": "ok"})
        elif op == "bind":
            self.broker.bind(msg["exchange"], msg["queue"], msg.get("routing_key", ""))
            self.send({"type": "ok"})
        elif op == "publish":
            n = self.broker.publish(msg["exchange"], msg.get("routing_key", ""), msg["message"])
            self.send({"type": "ok", "delivered": n})
        elif op == "consume":
            self.broker.attach_consumer(self, msg["consumer_tag"], msg["queue"],
                                        no_ack=msg.get("no_ack", False))
            self.send({"type": "ok"})
        elif op == "ack":
            self.broker.ack(msg["queue"], msg["delivery_tag"])
        elif op == "nack":
            self.broker.nack(msg["queue"], msg["delivery_tag"], requeue=msg.get("requeue", True))
        elif op == "ping":
            self.send({"type": "pong"})
        else:
            self.send({"type": "error", "msg": f"unknown op: {op}"})


# ============================================================
# Client
# ============================================================
class BlockingClient:
    def __init__(self, host="127.0.0.1", port=5673):
        self.host = host
        self.port = port
        self.sock = None
        self._consume_thread = None
        self._stop = False
        # 临时存放非 deliver 的响应
        self._reply_q: "queue.Queue[dict]" = queue.Queue()
        self._send_lock = threading.Lock()
        self._handlers: Dict[str, Callable] = {}     # consumer_tag -> callback
        self._consumer_seq = 0

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self._consume_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._consume_thread.start()

    def close(self):
        self._stop = True
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            self.sock.close()
        except Exception:
            pass

    def _reader_loop(self):
        while not self._stop:
            msg = recv_frame(self.sock)
            if msg is None:
                break
            if msg.get("type") == "deliver":
                tag = msg["consumer_tag"]
                cb = self._handlers.get(tag)
                if cb:
                    try:
                        ok = cb(msg["message"], msg["delivery_tag"], msg["queue"])
                    except Exception as e:
                        print(f"[consumer-err] {e}")
                        ok = False
                    if ok:
                        self.ack(msg["queue"], msg["delivery_tag"])
                    else:
                        self.nack(msg["queue"], msg["delivery_tag"], requeue=True)
            else:
                self._reply_q.put(msg)

    def _call(self, op, **kw):
        with self._send_lock:
            send_frame(self.sock, {"op": op, **kw})
        try:
            return self._reply_q.get(timeout=5)
        except queue.Empty:
            return None

    def declare_exchange(self, name, kind="direct"):
        return self._call("declare_exchange", name=name, kind=kind)

    def declare_queue(self, name, durable=False):
        return self._call("declare_queue", name=name, durable=durable)

    def bind(self, exchange, queue, routing_key=""):
        return self._call("bind", exchange=exchange, queue=queue, routing_key=routing_key)

    def publish(self, exchange, routing_key, message):
        return self._call("publish", exchange=exchange, routing_key=routing_key, message=message)

    def consume(self, queue, callback, no_ack=False):
        self._consumer_seq += 1
        tag = f"c{self._consumer_seq}"
        self._handlers[tag] = callback
        return self._call("consume", consumer_tag=tag, queue=queue, no_ack=no_ack)

    def ack(self, queue, delivery_tag):
        with self._send_lock:
            send_frame(self.sock, {"op": "ack", "queue": queue, "delivery_tag": delivery_tag})

    def nack(self, queue, delivery_tag, requeue=True):
        with self._send_lock:
            send_frame(self.sock, {"op": "nack", "queue": queue,
                                   "delivery_tag": delivery_tag, "requeue": requeue})


# ============================================================
# CLI / Demo
# ============================================================
def cmd_broker():
    host = "127.0.0.1"
    port = 5673
    persist = None
    for a in sys.argv[2:]:
        if a.startswith("--host="):
            host = a.split("=", 1)[1]
        elif a.startswith("--port="):
            port = int(a.split("=", 1)[1])
        elif a.startswith("--persist="):
            persist = a.split("=", 1)[1]
    Broker(host=host, port=port, persist_path=persist).serve()


def cmd_publish():
    if len(sys.argv) < 6:
        print("usage: publish <exchange> <kind> <routing_key> <json_message>")
        return
    exchange, kind, rk, msg = sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
    try:
        body = json.loads(msg)
    except Exception:
        body = msg
    c = BlockingClient()
    c.connect()
    c.declare_exchange(exchange, kind)
    r = c.publish(exchange, rk, body)
    print("[publish]", r)
    c.close()


def cmd_consume():
    if len(sys.argv) < 3:
        print("usage: consume <queue> [--bind=ex:rk] [--no-ack]")
        return
    qname = sys.argv[2]
    bindings = []
    no_ack = False
    for a in sys.argv[3:]:
        if a.startswith("--bind="):
            ex, rk = a.split("=", 1)[1].split(":", 1)
            bindings.append((ex, rk))
        elif a == "--no-ack":
            no_ack = True
    c = BlockingClient()
    c.connect()
    c.declare_queue(qname)
    for ex, rk in bindings:
        c.declare_exchange(ex, "topic")
        c.bind(ex, qname, rk)

    def cb(msg, tag, q):
        print(f"[recv {q}/{tag}] {msg}")
        return True

    c.consume(qname, cb, no_ack=no_ack)
    print(f"[consume] waiting messages on {qname}... Ctrl-C to quit")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        c.close()


def cmd_demo():
    """同进程跑：broker + producer + consumer"""
    broker = Broker(host="127.0.0.1", port=5675)
    t = threading.Thread(target=broker.serve, daemon=True)
    t.start()
    time.sleep(0.3)

    # consumer
    consumer = BlockingClient(port=5675)
    consumer.connect()
    consumer.declare_queue("orders")
    consumer.declare_exchange("ex", "topic")
    consumer.bind("ex", "orders", "order.*")

    received = []
    done = threading.Event()

    def handler(msg, tag, q):
        print(f"  [consumer] got #{len(received)+1}: {msg}")
        received.append(msg)
        if len(received) >= 5:
            done.set()
        return True

    consumer.consume("orders", handler)

    # producer
    producer = BlockingClient(port=5675)
    producer.connect()
    producer.declare_exchange("ex", "topic")
    print("[demo] publishing 5 orders...\n")
    for i in range(1, 6):
        rk = "order.created" if i % 2 else "order.paid"
        producer.publish("ex", rk, {"id": i, "rk": rk, "ts": time.time()})
        time.sleep(0.1)

    done.wait(timeout=3)
    print(f"\n[demo] received {len(received)} messages, done.")
    producer.close()
    consumer.close()
    broker.stop()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    if cmd == "broker": cmd_broker()
    elif cmd == "publish": cmd_publish()
    elif cmd == "consume": cmd_consume()
    elif cmd == "demo": cmd_demo()
    else: print("unknown command:", cmd)


if __name__ == "__main__":
    main()
