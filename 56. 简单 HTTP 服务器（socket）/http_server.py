# -*- coding: utf-8 -*-
"""
简单 HTTP 服务器（socket 实现）
- 仅支持 GET 方法
- 多线程处理连接
- 提供静态文件服务，目录浏览
"""
import os
import socket
import threading
import urllib.parse
import mimetypes
from datetime import datetime


class SimpleHTTPServer:
    def __init__(self, host="127.0.0.1", port=8000, root="."):
        self.host = host
        self.port = port
        self.root = os.path.abspath(root)

    def serve_forever(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((self.host, self.port))
        srv.listen(64)
        print(f"[+] HTTP server on http://{self.host}:{self.port}  root={self.root}")
        try:
            while True:
                conn, addr = srv.accept()
                threading.Thread(target=self.handle, args=(conn, addr), daemon=True).start()
        except KeyboardInterrupt:
            print("\n[!] Shutdown")
        finally:
            srv.close()

    def handle(self, conn, addr):
        try:
            conn.settimeout(5)
            data = b""
            while b"\r\n\r\n" not in data:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                data += chunk
                if len(data) > 64 * 1024:
                    break
            if not data:
                return
            head, _, _ = data.partition(b"\r\n\r\n")
            lines = head.decode("iso-8859-1").split("\r\n")
            if not lines:
                return
            request_line = lines[0]
            parts = request_line.split()
            if len(parts) < 3:
                self.send_status(conn, 400, "Bad Request")
                return
            method, path, _ = parts
            print(f"{addr[0]} - [{datetime.now():%Y-%m-%d %H:%M:%S}] \"{request_line}\"")

            if method.upper() != "GET":
                self.send_status(conn, 405, "Method Not Allowed")
                return

            self.serve_path(conn, urllib.parse.unquote(path.split("?", 1)[0]))
        except Exception as e:
            try:
                self.send_status(conn, 500, f"Internal Error: {e}")
            except Exception:
                pass
        finally:
            try:
                conn.close()
            except Exception:
                pass

    # ---- 响应 ----
    def send_status(self, conn, code, msg, body=None, content_type="text/plain; charset=utf-8"):
        body_bytes = (body or msg).encode("utf-8") if isinstance(body or msg, str) else (body or b"")
        headers = (
            f"HTTP/1.1 {code} {msg}\r\n"
            f"Content-Type: {content_type}\r\n"
            f"Content-Length: {len(body_bytes)}\r\n"
            f"Connection: close\r\n"
            f"Server: PySocketHTTP/1.0\r\n\r\n"
        ).encode("utf-8")
        conn.sendall(headers + body_bytes)

    def serve_path(self, conn, urlpath):
        # 安全：防止路径穿越
        rel = urlpath.lstrip("/")
        full = os.path.normpath(os.path.join(self.root, rel))
        if not full.startswith(self.root):
            self.send_status(conn, 403, "Forbidden")
            return
        if not os.path.exists(full):
            self.send_status(conn, 404, "Not Found")
            return
        if os.path.isdir(full):
            # 自动 index.html
            index = os.path.join(full, "index.html")
            if os.path.isfile(index):
                self.send_file(conn, index)
            else:
                self.send_listing(conn, full, urlpath)
        else:
            self.send_file(conn, full)

    def send_file(self, conn, path):
        ctype, _ = mimetypes.guess_type(path)
        ctype = ctype or "application/octet-stream"
        try:
            size = os.path.getsize(path)
            headers = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: {ctype}\r\n"
                f"Content-Length: {size}\r\n"
                f"Connection: close\r\n"
                f"Server: PySocketHTTP/1.0\r\n\r\n"
            ).encode("utf-8")
            conn.sendall(headers)
            with open(path, "rb") as f:
                while True:
                    buf = f.read(64 * 1024)
                    if not buf:
                        break
                    conn.sendall(buf)
        except FileNotFoundError:
            self.send_status(conn, 404, "Not Found")

    def send_listing(self, conn, full, urlpath):
        try:
            entries = sorted(os.listdir(full))
        except OSError:
            self.send_status(conn, 403, "Forbidden")
            return

        rows = []
        if urlpath not in ("/", ""):
            rows.append('<li><a href="../">../</a></li>')
        for name in entries:
            p = os.path.join(full, name)
            display = name + ("/" if os.path.isdir(p) else "")
            rows.append(f'<li><a href="{urllib.parse.quote(display)}">{display}</a></li>')

        html = (
            "<!doctype html><html><head><meta charset='utf-8'>"
            f"<title>Index of {urlpath}</title></head><body>"
            f"<h1>Index of {urlpath}</h1><ul>" + "".join(rows) + "</ul></body></html>"
        )
        self.send_status(conn, 200, "OK", body=html, content_type="text/html; charset=utf-8")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    SimpleHTTPServer(args.host, args.port, args.root).serve_forever()
