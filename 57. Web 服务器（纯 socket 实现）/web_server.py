# -*- coding: utf-8 -*-
"""
Web 服务器（纯 socket 实现）
- 与 56 相比，增加：
  * 完整的路由系统（@app.route）
  * GET / POST 方法
  * 简单的查询字符串与表单解析
  * 模板渲染（极简：{{var}} 替换）
  * 仍然是纯 socket，无 http.server / wsgi
"""
import os
import re
import socket
import threading
import urllib.parse
from datetime import datetime


class Request:
    def __init__(self, method, path, query, headers, body):
        self.method = method
        self.path = path
        self.query = query
        self.headers = headers
        self.body = body
        self.form = {}
        ctype = headers.get("content-type", "")
        if "application/x-www-form-urlencoded" in ctype and body:
            self.form = dict(urllib.parse.parse_qsl(body.decode("utf-8", errors="ignore")))


class Response:
    def __init__(self, body="", status=200, content_type="text/html; charset=utf-8", headers=None):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.body = body
        self.status = status
        self.content_type = content_type
        self.headers = headers or {}

    def to_bytes(self):
        reason = {200: "OK", 201: "Created", 301: "Moved", 302: "Found",
                  400: "Bad Request", 404: "Not Found", 405: "Method Not Allowed",
                  500: "Internal Server Error"}.get(self.status, "OK")
        out = [f"HTTP/1.1 {self.status} {reason}",
               f"Content-Type: {self.content_type}",
               f"Content-Length: {len(self.body)}",
               "Server: PyWebServer/1.0",
               "Connection: close"]
        for k, v in self.headers.items():
            out.append(f"{k}: {v}")
        head = "\r\n".join(out) + "\r\n\r\n"
        return head.encode("utf-8") + self.body


class WebApp:
    def __init__(self):
        self.routes = []  # list of (regex, methods, handler)

    def route(self, pattern, methods=("GET",)):
        # /user/<id>  ->  /user/(?P<id>[^/]+)
        regex = "^" + re.sub(r"<(\w+)>", r"(?P<\1>[^/]+)", pattern) + "$"
        compiled = re.compile(regex)

        def decorator(func):
            self.routes.append((compiled, tuple(m.upper() for m in methods), func))
            return func
        return decorator

    def render(self, template_str, **ctx):
        for k, v in ctx.items():
            template_str = template_str.replace("{{" + k + "}}", str(v))
        return template_str

    def dispatch(self, req: Request) -> Response:
        for pattern, methods, func in self.routes:
            m = pattern.match(req.path)
            if m:
                if req.method not in methods:
                    return Response("Method Not Allowed", status=405,
                                    content_type="text/plain; charset=utf-8")
                try:
                    return func(req, **m.groupdict())
                except Exception as e:
                    return Response(f"Internal Error: {e}", status=500,
                                    content_type="text/plain; charset=utf-8")
        return Response("404 Not Found", status=404,
                        content_type="text/plain; charset=utf-8")

    def serve(self, host="127.0.0.1", port=8080):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((host, port))
        srv.listen(64)
        print(f"[+] WebApp running on http://{host}:{port}")
        try:
            while True:
                conn, addr = srv.accept()
                threading.Thread(target=self._handle, args=(conn, addr), daemon=True).start()
        except KeyboardInterrupt:
            print("\n[!] Shutdown")
        finally:
            srv.close()

    def _handle(self, conn, addr):
        try:
            conn.settimeout(5)
            data = b""
            while b"\r\n\r\n" not in data:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                data += chunk
                if len(data) > 1024 * 1024:
                    break
            head, _, rest = data.partition(b"\r\n\r\n")
            lines = head.decode("iso-8859-1").split("\r\n")
            if not lines or len(lines[0].split()) < 2:
                return
            method, raw_path, *_ = lines[0].split()
            headers = {}
            for line in lines[1:]:
                if ":" in line:
                    k, v = line.split(":", 1)
                    headers[k.strip().lower()] = v.strip()

            # 读取剩余 body
            length = int(headers.get("content-length", 0))
            body = rest
            while len(body) < length:
                chunk = conn.recv(min(65536, length - len(body)))
                if not chunk:
                    break
                body += chunk

            url = urllib.parse.urlparse(raw_path)
            query = dict(urllib.parse.parse_qsl(url.query))
            req = Request(method.upper(), url.path, query, headers, body)
            print(f"{addr[0]} - [{datetime.now():%H:%M:%S}] {method} {raw_path}")

            resp = self.dispatch(req)
            conn.sendall(resp.to_bytes())
        except Exception as e:
            print(f"[!] handler error: {e}")
        finally:
            try:
                conn.close()
            except Exception:
                pass


# ---------- Demo 应用 ----------
app = WebApp()

INDEX_TPL = """<!doctype html>
<html><head><meta charset='utf-8'><title>{{title}}</title></head>
<body>
<h1>Hello, {{name}}!</h1>
<p>这是一个用纯 socket 实现的 Web 服务器。</p>
<ul>
  <li><a href="/">/</a> - 首页</li>
  <li><a href="/hello/Tom">/hello/Tom</a> - 路径参数</li>
  <li><a href="/echo?msg=hi">/echo?msg=hi</a> - 查询参数</li>
  <li><a href="/form">/form</a> - 表单 POST</li>
</ul>
</body></html>"""


@app.route("/")
def index(req):
    name = req.query.get("name", "World")
    return Response(app.render(INDEX_TPL, title="首页", name=name))


@app.route("/hello/<who>")
def hello(req, who):
    return Response(f"<h1>Hello, {who}!</h1>")


@app.route("/echo")
def echo(req):
    return Response(f"<pre>method={req.method}\nquery={req.query}</pre>")


@app.route("/form", methods=("GET", "POST"))
def form(req):
    if req.method == "POST":
        return Response(f"<p>收到: {req.form}</p><a href='/form'>返回</a>")
    return Response("""
        <form method="post" action="/form">
          <input name="user" placeholder="用户名"/>
          <input name="email" placeholder="邮箱"/>
          <button>提交</button>
        </form>""")


if __name__ == "__main__":
    app.serve()
