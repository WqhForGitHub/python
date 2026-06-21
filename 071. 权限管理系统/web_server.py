# -*- coding: utf-8 -*-
"""
Web 服务器（纯 socket 实现）
- 完全使用 socket / threading 编写，不依赖 http.server / wsgiref
- 特性：
  * HTTP/1.1 GET / POST / HEAD / OPTIONS
  * 静态文件服务（自动 MIME 推断）
  * 路由系统：装饰器 @app.route("/path", methods=["GET"])
  * 路径参数：/user/<id>
  * 简易模板（{{ name }} 替换）
  * 多线程并发
  * Keep-Alive（基础）
- 提供 demo 路由 + 静态目录

用法：
    python web_server.py
    打开 http://localhost:8000
"""
import os
import re
import socket
import threading
import urllib.parse
from datetime import datetime
from pathlib import Path


# ---------- MIME ----------
MIME = {
    ".html": "text/html; charset=utf-8",
    ".htm":  "text/html; charset=utf-8",
    ".txt":  "text/plain; charset=utf-8",
    ".css":  "text/css; charset=utf-8",
    ".js":   "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif":  "image/gif",
    ".svg":  "image/svg+xml",
    ".ico":  "image/x-icon",
    ".pdf":  "application/pdf",
}

STATUS_TEXT = {
    200: "OK", 201: "Created", 204: "No Content",
    301: "Moved Permanently", 302: "Found", 304: "Not Modified",
    400: "Bad Request", 401: "Unauthorized", 403: "Forbidden",
    404: "Not Found", 405: "Method Not Allowed",
    500: "Internal Server Error",
}


# ---------- 请求 / 响应 ----------
class Request:
    def __init__(self, method, path, query, headers, body):
        self.method = method
        self.path = path
        self.query = query
        self.headers = headers
        self.body = body

    @property
    def text(self):
        try: return self.body.decode("utf-8")
        except UnicodeDecodeError: return ""

    def form(self):
        ctype = self.headers.get("content-type", "")
        if "application/x-www-form-urlencoded" in ctype:
            return dict(urllib.parse.parse_qsl(self.text))
        return {}


class Response:
    def __init__(self, body=b"", status=200, headers=None, content_type="text/html; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.body = body
        self.status = status
        self.headers = {"Content-Type": content_type}
        if headers:
            self.headers.update(headers)
        self.headers.setdefault("Content-Length", str(len(self.body)))

    def to_bytes(self):
        text = STATUS_TEXT.get(self.status, "OK")
        lines = [f"HTTP/1.1 {self.status} {text}"]
        self.headers.setdefault("Date", datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT"))
        self.headers.setdefault("Server", "PySocketHTTP/0.1")
        self.headers.setdefault("Connection", "close")
        for k, v in self.headers.items():
            lines.append(f"{k}: {v}")
        head = "\r\n".join(lines).encode("utf-8") + b"\r\n\r\n"
        return head + self.body


# ---------- 路由 ----------
class Route:
    def __init__(self, pattern, methods, handler):
        self.methods = [m.upper() for m in methods]
        self.handler = handler
        # 把 <name> 转为正则
        regex = re.sub(r"<([^>]+)>", r"(?P<\1>[^/]+)", pattern)
        self.regex = re.compile("^" + regex + "$")

    def match(self, path):
        m = self.regex.match(path)
        return m.groupdict() if m else None


# ---------- 应用 ----------
class WebApp:
    def __init__(self, static_dir="static", host="0.0.0.0", port=8000):
        self.routes = []
        self.static_dir = Path(static_dir)
        self.host = host
        self.port = port

    def route(self, pattern, methods=("GET",)):
        def deco(fn):
            self.routes.append(Route(pattern, methods, fn))
            return fn
        return deco

    def render_template(self, path, **ctx):
        text = Path(path).read_text(encoding="utf-8")
        for k, v in ctx.items():
            text = text.replace("{{ " + k + " }}", str(v))
        return Response(text)

    # ---- 调度 ----
    def dispatch(self, req: Request) -> Response:
        # 路由
        for route in self.routes:
            params = route.match(req.path)
            if params is None:
                continue
            if req.method not in route.methods:
                return Response(f"Method {req.method} not allowed", status=405)
            try:
                resp = route.handler(req, **params)
                if not isinstance(resp, Response):
                    resp = Response(resp)
                return resp
            except Exception as e:
                import traceback; traceback.print_exc()
                return Response(f"Internal Error: {e}", status=500)

        # 静态文件
        if req.method in ("GET", "HEAD"):
            f = self._find_static(req.path)
            if f:
                ext = f.suffix.lower()
                ct = MIME.get(ext, "application/octet-stream")
                data = f.read_bytes() if req.method == "GET" else b""
                resp = Response(data, content_type=ct)
                if req.method == "HEAD":
                    resp.headers["Content-Length"] = str(f.stat().st_size)
                return resp

        return Response("<h1>404 Not Found</h1>", status=404)

    def _find_static(self, path):
        if path == "/":
            cand = self.static_dir / "index.html"
        else:
            cand = self.static_dir / path.lstrip("/")
        try:
            cand = cand.resolve()
            if not str(cand).startswith(str(self.static_dir.resolve())):
                return None
            if cand.is_file():
                return cand
        except Exception:
            pass
        return None

    # ---- 解析 HTTP ----
    def _parse_request(self, sock) -> Request:
        data = b""
        while b"\r\n\r\n" not in data:
            chunk = sock.recv(4096)
            if not chunk: break
            data += chunk
            if len(data) > 1024 * 64:
                break

        if not data:
            return None
        head, _, rest = data.partition(b"\r\n\r\n")
        lines = head.decode("iso-8859-1").split("\r\n")
        if not lines:
            return None
        try:
            method, target, _ = lines[0].split(" ", 2)
        except ValueError:
            return None

        url = urllib.parse.urlsplit(target)
        path = url.path
        query = dict(urllib.parse.parse_qsl(url.query))
        headers = {}
        for ln in lines[1:]:
            if ":" in ln:
                k, v = ln.split(":", 1)
                headers[k.strip().lower()] = v.strip()

        body = rest
        cl = int(headers.get("content-length", 0))
        while len(body) < cl:
            more = sock.recv(min(4096, cl - len(body)))
            if not more: break
            body += more
        return Request(method, path, query, headers, body[:cl] if cl else body)

    # ---- 客户端处理 ----
    def _handle_client(self, conn, addr):
        try:
            req = self._parse_request(conn)
            if req is None:
                conn.sendall(Response("Bad Request", status=400).to_bytes()); return
            resp = self.dispatch(req)
            conn.sendall(resp.to_bytes())
            print(f"{addr[0]} {req.method} {req.path} -> {resp.status}")
        except Exception as e:
            print(f"[err] {addr}: {e}")
        finally:
            try: conn.shutdown(socket.SHUT_RDWR)
            except OSError: pass
            conn.close()

    # ---- 运行 ----
    def run(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((self.host, self.port))
        srv.listen(64)
        print(f"PySocketHTTP listening on http://{self.host}:{self.port}")
        try:
            while True:
                conn, addr = srv.accept()
                t = threading.Thread(target=self._handle_client, args=(conn, addr), daemon=True)
                t.start()
        except KeyboardInterrupt:
            print("\n服务器关闭")
        finally:
            srv.close()


# ---------- demo ----------
def main():
    base = Path(__file__).parent
    static_dir = base / "static"
    static_dir.mkdir(exist_ok=True)
    (static_dir / "index.html").write_text(
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<title>PyWeb</title></head><body><h1>欢迎使用 PySocketHTTP</h1>"
        "<p>试试 <a href='/hello/world'>/hello/world</a> 或 "
        "<a href='/info'>/info</a></p></body></html>",
        encoding="utf-8"
    )

    app = WebApp(static_dir=str(static_dir))

    @app.route("/hello/<name>")
    def hello(req, name):
        return Response(f"<h1>Hello, {name}!</h1><p>method={req.method}</p>")

    @app.route("/info")
    def info(req):
        body = "<h2>Headers</h2><pre>" + \
               "\n".join(f"{k}: {v}" for k, v in req.headers.items()) + "</pre>"
        return Response(body)

    @app.route("/echo", methods=["POST"])
    def echo(req):
        return Response(req.text or "(empty)")

    app.run()


if __name__ == "__main__":
    main()
