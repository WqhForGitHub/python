# -*- coding: utf-8 -*-
"""
REST API（仅 Python 标准库）
- 基于 http.server 实现 RESTful 接口
- 资源：/users
  GET    /users          列出所有用户
  GET    /users/<id>     获取单个用户
  POST   /users          创建用户   body: {"name":"...","age":..}
  PUT    /users/<id>     更新用户
  DELETE /users/<id>     删除用户
- 数据存储：JSON 文件持久化
"""
import json
import os
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


DB_FILE = os.path.join(os.path.dirname(__file__), "data.json")
LOCK = threading.Lock()


def load_db():
    if not os.path.exists(DB_FILE):
        return {"next_id": 1, "users": {}}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


class Handler(BaseHTTPRequestHandler):
    server_version = "PyREST/1.0"

    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return None

    def log_message(self, fmt, *args):
        # 简化日志
        print(f"[{self.log_date_time_string()}] {self.address_string()} {fmt % args}")

    # 路由
    def route(self, method):
        path = self.path.split("?", 1)[0]
        m = re.match(r"^/users/?$", path)
        if m:
            if method == "GET":
                return self.list_users()
            if method == "POST":
                return self.create_user()
            return self._json({"error": "method not allowed"}, 405)

        m = re.match(r"^/users/(\d+)/?$", path)
        if m:
            uid = m.group(1)
            if method == "GET":
                return self.get_user(uid)
            if method == "PUT":
                return self.update_user(uid)
            if method == "DELETE":
                return self.delete_user(uid)
            return self._json({"error": "method not allowed"}, 405)

        if path == "/":
            return self._json({
                "name": "PyREST Demo",
                "endpoints": ["GET /users", "POST /users",
                              "GET/PUT/DELETE /users/<id>"]
            })
        return self._json({"error": "not found"}, 404)

    def do_GET(self):
        self.route("GET")

    def do_POST(self):
        self.route("POST")

    def do_PUT(self):
        self.route("PUT")

    def do_DELETE(self):
        self.route("DELETE")

    # 业务处理
    def list_users(self):
        with LOCK:
            db = load_db()
        users = list(db["users"].values())
        self._json({"count": len(users), "items": users})

    def get_user(self, uid):
        with LOCK:
            db = load_db()
        u = db["users"].get(uid)
        if not u:
            return self._json({"error": "not found"}, 404)
        self._json(u)

    def create_user(self):
        data = self._read_json()
        if data is None or not isinstance(data, dict):
            return self._json({"error": "invalid json"}, 400)
        name = data.get("name")
        if not name:
            return self._json({"error": "name is required"}, 400)
        with LOCK:
            db = load_db()
            uid = str(db["next_id"])
            db["next_id"] += 1
            user = {"id": int(uid), "name": name, "age": data.get("age")}
            db["users"][uid] = user
            save_db(db)
        self._json(user, 201)

    def update_user(self, uid):
        data = self._read_json()
        if data is None:
            return self._json({"error": "invalid json"}, 400)
        with LOCK:
            db = load_db()
            if uid not in db["users"]:
                return self._json({"error": "not found"}, 404)
            db["users"][uid].update({k: v for k, v in data.items() if k in ("name", "age")})
            save_db(db)
            self._json(db["users"][uid])

    def delete_user(self, uid):
        with LOCK:
            db = load_db()
            if uid not in db["users"]:
                return self._json({"error": "not found"}, 404)
            user = db["users"].pop(uid)
            save_db(db)
        self._json({"deleted": user})


def main(host="127.0.0.1", port=5000):
    srv = ThreadingHTTPServer((host, port), Handler)
    print(f"[+] REST API on http://{host}:{port}")
    print("    示例:")
    print("    curl http://127.0.0.1:5000/users")
    print('    curl -X POST -H "Content-Type: application/json" -d "{\\"name\\":\\"Tom\\",\\"age\\":20}" http://127.0.0.1:5000/users')
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == "__main__":
    main()
