"""
微服务框架（轻量级）- 纯 Python 实现
=====================================
提供：
- 服务注册中心（Registry）：注册 / 注销 / 心跳 / 服务发现
- 负载均衡：随机 / 轮询 / 最少连接
- 熔断器（Circuit Breaker）：CLOSED / OPEN / HALF_OPEN
- 重试 + 超时
- RPC 调用（基于 socket + JSON）
- 服务装饰器 @service / @rpc

仅依赖标准库；可作为 FastAPI/Spring Cloud 简化教学版。
"""

import json
import socket
import threading
import time
import random
import uuid
from collections import defaultdict


# ============================================================
# 1. 服务注册中心
# ============================================================
class Registry:
    """内存型注册中心（生产级应使用 etcd / consul / zk）"""

    def __init__(self, ttl=10):
        self.services = defaultdict(dict)  # name -> {instance_id: meta}
        self.ttl = ttl
        self.lock = threading.Lock()
        threading.Thread(target=self._gc_loop, daemon=True).start()

    def register(self, name, host, port, meta=None):
        instance_id = str(uuid.uuid4())[:8]
        info = {
            "id": instance_id,
            "name": name,
            "host": host,
            "port": port,
            "last_heartbeat": time.time(),
            "meta": meta or {},
            "active_calls": 0,
        }
        with self.lock:
            self.services[name][instance_id] = info
        return instance_id

    def heartbeat(self, name, instance_id):
        with self.lock:
            inst = self.services.get(name, {}).get(instance_id)
            if inst:
                inst["last_heartbeat"] = time.time()
                return True
        return False

    def deregister(self, name, instance_id):
        with self.lock:
            self.services.get(name, {}).pop(instance_id, None)

    def discover(self, name):
        with self.lock:
            return [dict(v) for v in self.services.get(name, {}).values()]

    def _gc_loop(self):
        while True:
            time.sleep(self.ttl / 2)
            now = time.time()
            with self.lock:
                for name in list(self.services.keys()):
                    expired = [i for i, info in self.services[name].items()
                               if now - info["last_heartbeat"] > self.ttl]
                    for i in expired:
                        del self.services[name][i]


# ============================================================
# 2. 负载均衡器
# ============================================================
class LoadBalancer:
    def __init__(self, strategy="round_robin"):
        self.strategy = strategy
        self._rr_idx = defaultdict(int)
        self.lock = threading.Lock()

    def pick(self, instances, service_name=""):
        if not instances:
            return None
        if self.strategy == "random":
            return random.choice(instances)
        if self.strategy == "least_conn":
            return min(instances, key=lambda x: x.get("active_calls", 0))
        # round robin
        with self.lock:
            idx = self._rr_idx[service_name] % len(instances)
            self._rr_idx[service_name] += 1
        return instances[idx]


# ============================================================
# 3. 熔断器
# ============================================================
class CircuitBreaker:
    """状态机：CLOSED -> OPEN -> HALF_OPEN -> CLOSED"""

    def __init__(self, fail_threshold=3, reset_timeout=5):
        self.state = "CLOSED"
        self.fail_count = 0
        self.fail_threshold = fail_threshold
        self.reset_timeout = reset_timeout
        self.opened_at = 0
        self.lock = threading.Lock()

    def call(self, fn, *args, **kwargs):
        with self.lock:
            if self.state == "OPEN":
                if time.time() - self.opened_at > self.reset_timeout:
                    self.state = "HALF_OPEN"
                else:
                    raise RuntimeError("Circuit breaker OPEN")

        try:
            result = fn(*args, **kwargs)
        except Exception:
            with self.lock:
                self.fail_count += 1
                if self.fail_count >= self.fail_threshold:
                    self.state = "OPEN"
                    self.opened_at = time.time()
            raise

        with self.lock:
            self.fail_count = 0
            self.state = "CLOSED"
        return result


# ============================================================
# 4. RPC 客户端 / 服务端
# ============================================================
class RPCServer:
    def __init__(self, host="127.0.0.1", port=0):
        self.host = host
        self.port = port
        self.handlers = {}      # method -> fn
        self.sock = None
        self.running = False
        self.thread = None

    def register(self, name, fn):
        self.handlers[name] = fn

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen(8)
        self.host, self.port = self.sock.getsockname()
        self.running = True
        self.thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.thread.start()
        return self.host, self.port

    def stop(self):
        self.running = False
        try:
            self.sock.close()
        except Exception:
            pass

    def _accept_loop(self):
        while self.running:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                break
            threading.Thread(target=self._handle, args=(conn,), daemon=True).start()

    def _handle(self, conn):
        try:
            with conn:
                data = b""
                while True:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                    if data.endswith(b"\n"):
                        break
                req = json.loads(data.decode().strip())
                method = req.get("method")
                args = req.get("args", [])
                kwargs = req.get("kwargs", {})
                fn = self.handlers.get(method)
                if not fn:
                    resp = {"error": f"method {method} not found"}
                else:
                    try:
                        result = fn(*args, **kwargs)
                        resp = {"result": result}
                    except Exception as e:
                        resp = {"error": str(e)}
                conn.sendall((json.dumps(resp) + "\n").encode())
        except Exception:
            pass


def rpc_call(host, port, method, args=None, kwargs=None, timeout=3):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        payload = json.dumps({
            "method": method,
            "args": args or [],
            "kwargs": kwargs or {},
        })
        s.sendall((payload + "\n").encode())
        data = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
            if data.endswith(b"\n"):
                break
        resp = json.loads(data.decode().strip())
        if "error" in resp:
            raise RuntimeError(resp["error"])
        return resp["result"]
    finally:
        s.close()


# ============================================================
# 5. 客户端代理（含重试 / 熔断 / 负载均衡）
# ============================================================
class ServiceClient:
    def __init__(self, registry, service_name, lb=None,
                 retries=2, timeout=3):
        self.registry = registry
        self.service_name = service_name
        self.lb = lb or LoadBalancer("round_robin")
        self.retries = retries
        self.timeout = timeout
        self.breakers = defaultdict(lambda: CircuitBreaker(3, 5))

    def call(self, method, *args, **kwargs):
        last_err = None
        for attempt in range(self.retries + 1):
            instances = self.registry.discover(self.service_name)
            if not instances:
                raise RuntimeError(f"No instances of {self.service_name}")
            inst = self.lb.pick(instances, self.service_name)
            key = f"{inst['host']}:{inst['port']}"
            breaker = self.breakers[key]
            try:
                inst["active_calls"] += 1
                return breaker.call(rpc_call, inst["host"], inst["port"],
                                    method, list(args), kwargs, self.timeout)
            except Exception as e:
                last_err = e
                continue
            finally:
                inst["active_calls"] = max(0, inst.get("active_calls", 1) - 1)
        raise RuntimeError(f"call {self.service_name}.{method} failed: {last_err}")


# ============================================================
# 6. 装饰器：方便构建服务
# ============================================================
def service(registry, name, host="127.0.0.1", port=0):
    """装饰一个类作为微服务，自动启动 RPC 服务器并注册"""

    def deco(cls):
        instance = cls()
        server = RPCServer(host, port)
        for attr in dir(instance):
            if attr.startswith("_"):
                continue
            method = getattr(instance, attr)
            if callable(method) and getattr(method, "_rpc", False):
                server.register(attr, method)
        h, p = server.start()
        instance_id = registry.register(name, h, p)
        instance._registry = registry
        instance._instance_id = instance_id
        instance._server = server

        def heartbeat_loop():
            while True:
                time.sleep(3)
                if not registry.heartbeat(name, instance_id):
                    break

        threading.Thread(target=heartbeat_loop, daemon=True).start()
        return instance

    return deco


def rpc(fn):
    """标记方法为可远程调用"""
    fn._rpc = True
    return fn


# ============================================================
# Demo
# ============================================================
def demo():
    print("=" * 60)
    print("微服务框架 Demo: 注册中心 + RPC + 负载均衡 + 熔断")
    print("=" * 60)

    registry = Registry(ttl=30)

    # 启动两个 "user-service" 实例做负载均衡
    @service(registry, "user-service")
    class UserServiceA:
        @rpc
        def get_user(self, uid):
            return {"id": uid, "name": f"user_{uid}", "served_by": "A"}

        @rpc
        def add(self, a, b):
            return a + b

    @service(registry, "user-service")
    class UserServiceB:
        @rpc
        def get_user(self, uid):
            return {"id": uid, "name": f"user_{uid}", "served_by": "B"}

        @rpc
        def add(self, a, b):
            return a + b

    # 启动一个 "calc-service"
    @service(registry, "calc-service")
    class CalcService:
        @rpc
        def divide(self, a, b):
            return a / b  # 故意可能除零，触发熔断

    time.sleep(0.3)

    print("\n--- 已注册的服务 ---")
    for name in ["user-service", "calc-service"]:
        for inst in registry.discover(name):
            print(f"  {name} @ {inst['host']}:{inst['port']} (id={inst['id']})")

    print("\n--- 调用 user-service.get_user (Round Robin 负载均衡) ---")
    client = ServiceClient(registry, "user-service",
                           lb=LoadBalancer("round_robin"))
    for i in range(5):
        res = client.call("get_user", i)
        print(f"  call {i}: {res}")

    print("\n--- 调用 user-service.add ---")
    print(f"  add(3, 4) = {client.call('add', 3, 4)}")

    print("\n--- 熔断测试: 连续除零失败 ---")
    calc = ServiceClient(registry, "calc-service", retries=0)
    for i in range(5):
        try:
            r = calc.call("divide", 10, 0)
            print(f"  call {i}: {r}")
        except Exception as e:
            print(f"  call {i}: ERROR -> {e}")

    print("\n--- 正常调用恢复 ---")
    try:
        print(f"  divide(10, 2) = {calc.call('divide', 10, 2)}")
    except Exception as e:
        print(f"  断路器仍然打开: {e}")
        print("  等待 5 秒后断路器进入半开状态...")
        time.sleep(5.2)
        print(f"  divide(10, 2) = {calc.call('divide', 10, 2)}")

    print("\n演示结束。")


if __name__ == "__main__":
    demo()
