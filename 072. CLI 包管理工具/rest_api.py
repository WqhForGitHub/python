# -*- coding: utf-8 -*-
"""
REST API（仅 Python 实现）
- 仅使用 Python 标准库（socket / json / threading），不引入第三方框架
- 内置一个 mini-Flask 风格的 RESTful 框架
- 演示资源：/api/users，支持完整 CRUD
  GET    /api/users          - 列表（支持 ?limit=&offset=&q=）
  GET    /api/users/<id>     - 详情
  POST   /api/users          - 创建
  PUT    /api/users/<id>     - 更新（全量）
  PATCH  /api/users/<id>     - 更新（部分）
  DELETE /api/users/<id>     - 删除
- JSON 请求 / 响应
- 错误以统一 JSON 包装

用法：
    python rest_api.py
    curl http://localhost:8001/api/users
"""
import json
import re
import socket
import threading
import urllib.parse
from datetime import datetime


# ---------- HTTP 工具 ----------
STATUS_TEXT = {200: "OK", 201: "Created", 204: "No Content",
               400: "Bad Request", 404: "Not Found", 405: "Method Not Allowed",
               409: "Conflict", 422: "Unprocessable Entity", 500: "Internal Server Error"}


class Request:
    def __init__(self, method, path, query, headers, body):
        self.method, self.path, self.query, self.headers, self.body = \
            method, path, query, headers, body

    def json(self):
        if not self.body: return None
        try: return json.loads(self.body.decode("utf-8"))
        except Exception: raise ValueError("invalid json body")


class Response:
    def __init__(self, payload=None, status=200, headers=None):
        self.status = status
        self.headers = {"Content-Type": "application/json; charset=utf-8"}
        if headers: self.headers.update(headers)
        if payload is None and status == 204:
            self.body = b""
        else:
            self.body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.headers["Content-Length"] = str(len(self.body))

    def to_bytes(self):
        head = [f"HTTP/1.1 {self.status} {STATUS_TEXT.get(self.status, 'OK')}"]
        self.headers.setdefault("Date", datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT"))
        self.headers.setdefault("Server", "PyREST/0.1")
        self.headers.setdefault("Connection", "close")
        for k, v in self.headers.items():
            head.append(f"{k}: {v}")
        return ("\r\n".join(head) + "\r\n\r\n").encode("utf-8") + self.body


# ---------- 路由 ----------
class Router:
    def __init__(self):
        self.routes = []  # (method, regex, handler)

    def add(self, method, pattern, handler):
        regex = re.sub(r"<([^>]+)>", r"(?P<\1>[^/]+)", pattern)
        self.routes.append((method.upper(), re.compile("^" + regex + "$"), handler))

    def dispatch(self, req):
        path_match_no_method = False
        for method, regex, handler in self.routes:
            m = regex.match(req.path)
            if not m: continue
            if method != req.method:
                path_match_no_method = True; continue
            try:
                return handler(req, **m.groupdict())
            except ValueError as ve:
                return Response({"error": str(ve)}, status=400)
            except KeyError as ke:
                return Response({"error": f"missing field: {ke}"}, status=422)
            except LookupError as le:
                return Response({"error": str(le)}, status=404)
            except Exception as e:
                import traceback; traceback.print_exc()
                return Response({"error": str(e)}, status=500)
        if path_match_no_method:
            return Response({"error": "method not allowed"}, status=405)
        return Response({"error": "not found"}, status=404)


# ---------- HTTP 服务器 ----------
class APIServer:
    def __init__(self, host="0.0.0.0", port=8001):
        self.host, self.port = host, port
        self.router = Router()

    def route(self, method, pattern):
        def deco(fn):
            self.router.add(method, pattern, fn); return fn
        return deco

    def get(self, p):    return self.route("GET", p)
    def post(self, p):   return self.route("POST", p)
    def put(self, p):    return self.route("PUT", p)
    def patch(self, p):  return self.route("PATCH", p)
    def delete(self, p): return self.route("DELETE", p)

    def _parse(self, conn):
        data = b""
        while b"\r\n\r\n" not in data:
            chunk = conn.recv(4096)
            if not chunk: break
            data += chunk
            if len(data) > 1024 * 256: break
        if not data: return None
        head, _, body = data.partition(b"\r\n\r\n")
        lines = head.decode("iso-8859-1").split("\r\n")
        method, target, _ = lines[0].split(" ", 2)
        url = urllib.parse.urlsplit(target)
        query = dict(urllib.parse.parse_qsl(url.query))
        headers = {}
        for l in lines[1:]:
            if ":" in l:
                k, v = l.split(":", 1)
                headers[k.strip().lower()] = v.strip()
        cl = int(headers.get("content-length", 0))
        while len(body) < cl:
            more = conn.recv(min(4096, cl - len(body)))
            if not more: break
            body += more
        return Request(method, url.path, query, headers, body[:cl] if cl else body)

    def _client(self, conn, addr):
        try:
            req = self._parse(conn)
            if req is None:
                conn.sendall(Response({"error": "bad request"}, status=400).to_bytes()); return
            resp = self.router.dispatch(req)
            conn.sendall(resp.to_bytes())
            print(f"{addr[0]} {req.method:6} {req.path:30} -> {resp.status}")
        finally:
            try: conn.shutdown(socket.SHUT_RDWR)
            except OSError: pass
            conn.close()

    def run(self):
        srv = socket.socket()
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((self.host, self.port))
        srv.listen(64)
        print(f"PyREST listening on http://{self.host}:{self.port}")
        try:
            while True:
                c, a = srv.accept()
                threading.Thread(target=self._client, args=(c, a), daemon=True).start()
        except KeyboardInterrupt:
            print("\n停止")
        finally:
            srv.close()


# ---------- 资源：用户 ----------
class UserStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._auto = 0
        self._data = {}

    def list(self, q=None, limit=20, offset=0):
        items = list(self._data.values())
        if q:
            items = [u for u in items if q.lower() in u["name"].lower()]
        return items[offset: offset + limit], len(items)

    def create(self, payload):
        if "name" not in payload:
            raise KeyError("name")
        with self._lock:
            self._auto += 1
            user = {
                "id": self._auto,
                "name": payload["name"],
                "email": payload.get("email", ""),
                "age": int(payload.get("age", 0)),
            }
            self._data[user["id"]] = user
            return user

    def get(self, uid):
        if uid not in self._data:
            raise LookupError(f"user {uid} not found")
        return self._data[uid]

    def update(self, uid, payload, partial=False):
        user = self.get(uid)
        if partial:
            for k in ("name", "email", "age"):
                if k in payload: user[k] = payload[k]
        else:
            if "name" not in payload: raise KeyError("name")
            user.update({"name": payload["name"],
                         "email": payload.get("email", ""),
                         "age": int(payload.get("age", 0))})
        return user

    def delete(self, uid):
        self.get(uid)
        del self._data[uid]


# ---------- 应用 ----------
def build_app():
    app = APIServer()
    store = UserStore()

    # 预填几条数据
    store.create({"name": "Alice", "email": "a@x.com", "age": 30})
    store.create({"name": "Bob", "email": "b@x.com", "age": 25})

    @app.get("/api/users")
    def list_users(req):
        limit = int(req.query.get("limit", 20))
        offset = int(req.query.get("offset", 0))
        q = req.query.get("q")
        items, total = store.list(q, limit, offset)
        return Response({"items": items, "total": total,
                         "limit": limit, "offset": offset})

    @app.get("/api/users/<uid>")
    def get_user(req, uid):
        return Response(store.get(int(uid)))

    @app.post("/api/users")
    def create_user(req):
        body = req.json() or {}
        return Response(store.create(body), status=201)

    @app.put("/api/users/<uid>")
    def put_user(req, uid):
        return Response(store.update(int(uid), req.json() or {}, partial=False))

    @app.patch("/api/users/<uid>")
    def patch_user(req, uid):
        return Response(store.update(int(uid), req.json() or {}, partial=True))

    @app.delete("/api/users/<uid>")
    def delete_user(req, uid):
        store.delete(int(uid))
        return Response(status=204)

    @app.get("/")
    def root(req):
        return Response({"name": "PyREST", "endpoints": [
            "GET /api/users", "POST /api/users",
            "GET/PUT/PATCH/DELETE /api/users/<id>"
        ]})

    return app


if __name__ == "__main__":
    build_app().run()
