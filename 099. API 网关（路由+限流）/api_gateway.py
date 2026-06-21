"""
API 网关（路由 + 限流）- 纯 Python 实现
=====================================
基于标准库 http.server，提供：
- 路径正则路由（含 path 参数 /users/<id>）
- 服务发现：转发到注册的 upstream
- 限流：令牌桶 + 滑动窗口（每 IP / 每路由）
- 鉴权：Bearer Token / API Key
- 简单中间件机制（请求/响应钩子）
- 访问日志 & 性能指标
"""

import json
import re
import time
import threading
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from collections import defaultdict, deque


# ---------- 限流器 ----------
class TokenBucket:
    """令牌桶限流器"""
    def __init__(self, capacity, refill_rate):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate  # tokens/second
        self.last = time.time()
        self.lock = threading.Lock()

    def acquire(self, n=1):
        with self.lock:
            now = time.time()
            self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.refill_rate)
            self.last = now
            if self.tokens >= n:
                self.tokens -= n
                return True
            return False


class SlidingWindow:
    """滑动窗口限流：window_sec 内最多 max_requests 次"""
    def __init__(self, window_sec, max_requests):
        self.window = window_sec
        self.max = max_requests
        self.records = defaultdict(deque)  # key -> deque[timestamps]
        self.lock = threading.Lock()

    def acquire(self, key):
        with self.lock:
            now = time.time()
            q = self.records[key]
            while q and q[0] <= now - self.window:
                q.popleft()
            if len(q) >= self.max:
                return False
            q.append(now)
            return True


# ---------- 路由 ----------
class Route:
    def __init__(self, method, pattern, handler=None, upstream=None,
                 auth=None, rate_limit=None):
        self.method = method.upper()
        self.pattern_str = pattern
        self.regex = self._compile(pattern)
        self.handler = handler
        self.upstream = upstream
        self.auth = auth                  # "bearer" / "api_key" / None
        self.rate_limit = rate_limit      # (capacity, rate) for token bucket

    @staticmethod
    def _compile(pattern):
        # /users/<id> -> ^/users/(?P<id>[^/]+)$
        regex = re.sub(r"<(\w+)>", r"(?P<\1>[^/]+)", pattern)
        return re.compile("^" + regex + "$")

    def match(self, method, path):
        if method.upper() != self.method:
            return None
        m = self.regex.match(path)
        if not m:
            return None
        return m.groupdict()


# ---------- 网关 ----------
class APIGateway:
    def __init__(self):
        self.routes = []
        self.middlewares = []
        self.global_limiter = SlidingWindow(window_sec=1, max_requests=100)
        self.route_limiters = {}
        self.tokens = {"valid-token-123"}  # 鉴权 token 集合
        self.api_keys = {"demo-key": "demo-user"}
        self.metrics = defaultdict(lambda: {"count": 0, "errors": 0, "total_time": 0.0})

    def add_route(self, method, pattern, handler=None, upstream=None,
                  auth=None, rate_limit=None):
        route = Route(method, pattern, handler, upstream, auth, rate_limit)
        self.routes.append(route)
        if rate_limit:
            cap, rate = rate_limit
            self.route_limiters[route.pattern_str] = TokenBucket(cap, rate)
        return route

    def use(self, mw):
        """注册中间件：mw(req, ctx) -> None | (status, body)"""
        self.middlewares.append(mw)

    # ---- 处理请求 ----
    def handle(self, method, path, headers, body, client_ip):
        t0 = time.time()
        # 全局限流
        if not self.global_limiter.acquire(client_ip):
            return 429, {"error": "Too Many Requests (global)"}

        # 路由匹配
        route = None
        params = None
        for r in self.routes:
            params = r.match(method, path)
            if params is not None:
                route = r
                break
        if not route:
            return 404, {"error": "Not Found"}

        # 鉴权
        if route.auth == "bearer":
            token = headers.get("Authorization", "")
            if not token.startswith("Bearer ") or token[7:] not in self.tokens:
                return 401, {"error": "Unauthorized"}
        elif route.auth == "api_key":
            key = headers.get("X-API-Key", "")
            if key not in self.api_keys:
                return 401, {"error": "Invalid API Key"}

        # 路由级限流
        if route.rate_limit:
            limiter = self.route_limiters[route.pattern_str]
            if not limiter.acquire():
                return 429, {"error": "Too Many Requests (route)"}

        # 中间件
        ctx = {"params": params, "client_ip": client_ip}
        req = {"method": method, "path": path, "headers": headers, "body": body}
        for mw in self.middlewares:
            res = mw(req, ctx)
            if res is not None:
                status, payload = res
                self._record(route, t0, status >= 400)
                return status, payload

        # 处理：本地 handler 或 upstream 转发
        try:
            if route.handler:
                status, payload = route.handler(req, ctx)
            elif route.upstream:
                status, payload = self._forward(route.upstream, req)
            else:
                status, payload = 500, {"error": "No handler"}
        except Exception as e:
            status, payload = 500, {"error": str(e)}

        self._record(route, t0, status >= 400)
        return status, payload

    def _forward(self, upstream, req):
        url = upstream.rstrip("/") + req["path"]
        data = req["body"] if req["body"] else None
        if data and not isinstance(data, bytes):
            data = json.dumps(data).encode()
        r = urllib.request.Request(url, data=data, method=req["method"])
        for k, v in req["headers"].items():
            r.add_header(k, v)
        try:
            with urllib.request.urlopen(r, timeout=5) as resp:
                body = resp.read()
                try:
                    return resp.status, json.loads(body)
                except Exception:
                    return resp.status, {"raw": body.decode("utf-8", "ignore")}
        except urllib.error.HTTPError as e:
            return e.code, {"error": e.reason}
        except Exception as e:
            return 502, {"error": f"Upstream error: {e}"}

    def _record(self, route, t0, is_error):
        m = self.metrics[route.pattern_str]
        m["count"] += 1
        m["total_time"] += time.time() - t0
        if is_error:
            m["errors"] += 1


# ---------- HTTP 适配器 ----------
class GatewayHandler(BaseHTTPRequestHandler):
    gateway = None  # 由外部注入

    def _do(self, method):
        length = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(length) if length else b""
        try:
            body = json.loads(body) if body else None
        except Exception:
            pass
        headers = {k: v for k, v in self.headers.items()}
        client_ip = self.client_address[0]
        status, payload = self.gateway.handle(method, self.path, headers, body, client_ip)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        body_bytes = json.dumps(payload, ensure_ascii=False).encode()
        self.send_header("Content-Length", str(len(body_bytes)))
        self.end_headers()
        self.wfile.write(body_bytes)

    def do_GET(self):    self._do("GET")
    def do_POST(self):   self._do("POST")
    def do_PUT(self):    self._do("PUT")
    def do_DELETE(self): self._do("DELETE")

    def log_message(self, format, *args):
        # 简化日志
        print(f"[GW] {self.command} {self.path} -> {self.client_address[0]}")


def make_server(gateway, port=8080):
    GatewayHandler.gateway = gateway
    server = HTTPServer(("0.0.0.0", port), GatewayHandler)
    return server


# ---------- Demo ----------
def demo():
    gw = APIGateway()

    # 注册路由
    def hello(req, ctx):
        return 200, {"message": "Hello from gateway", "path": req["path"]}

    def get_user(req, ctx):
        uid = ctx["params"]["id"]
        return 200, {"user_id": uid, "name": f"user_{uid}"}

    def echo(req, ctx):
        return 200, {"echo": req["body"]}

    gw.add_route("GET", "/hello", handler=hello)
    gw.add_route("GET", "/users/<id>", handler=get_user, auth="bearer")
    gw.add_route("POST", "/echo", handler=echo,
                 rate_limit=(2, 1))  # 每秒 1 个，桶容量 2
    gw.add_route("GET", "/private", handler=hello, auth="api_key")

    # 中间件：日志
    def logger(req, ctx):
        print(f"  [MW] {req['method']} {req['path']} from {ctx['client_ip']}")

    gw.use(logger)

    print("=" * 60)
    print("API Gateway 离线测试（不启动 HTTP 服务器）")
    print("=" * 60)

    cases = [
        ("GET", "/hello", {}, None),
        ("GET", "/users/42", {}, None),                                    # 401
        ("GET", "/users/42", {"Authorization": "Bearer valid-token-123"}, None),
        ("POST", "/echo", {}, {"data": "hi"}),
        ("POST", "/echo", {}, {"data": "hi"}),                              # 第二次 OK
        ("POST", "/echo", {}, {"data": "hi"}),                              # 可能 429
        ("GET", "/private", {}, None),                                      # 401
        ("GET", "/private", {"X-API-Key": "demo-key"}, None),
        ("GET", "/notfound", {}, None),
    ]
    for method, path, headers, body in cases:
        status, resp = gw.handle(method, path, headers, body, "127.0.0.1")
        print(f"  {method} {path}  -> {status}  {resp}")

    print("\n--- Metrics ---")
    for route, m in gw.metrics.items():
        avg = m["total_time"] / m["count"] * 1000 if m["count"] else 0
        print(f"  {route}: count={m['count']}, errors={m['errors']}, avg={avg:.2f}ms")

    # 启动真实服务器（取消注释即可）
    # print("\n[启动 HTTP 服务器 在 :8080，Ctrl+C 退出]")
    # make_server(gw, 8080).serve_forever()


if __name__ == "__main__":
    demo()
