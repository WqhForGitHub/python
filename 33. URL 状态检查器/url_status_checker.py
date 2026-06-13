"""
URL 状态检查器
功能：批量检查 URL 状态，支持并发（多线程）、超时、重试、HEAD/GET、
      跟随重定向、记录响应时间、按状态分组、导出报告等
"""

import os
import time
import urllib.request
import urllib.parse
import urllib.error
import socket
import threading
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime


class URLStatusChecker:
    """URL 状态检查器"""

    # 状态码分类
    STATUS_CATEGORIES = {
        "1xx": "信息响应",
        "2xx": "成功",
        "3xx": "重定向",
        "4xx": "客户端错误",
        "5xx": "服务端错误",
        "0": "网络错误",
    }

    def __init__(
        self,
        timeout: int = 10,
        retries: int = 1,
        method: str = "HEAD",
        follow_redirects: bool = True,
        user_agent: str = "Mozilla/5.0 (compatible; URLChecker/1.0)",
    ):
        self.timeout = timeout
        self.retries = retries
        self.method = method.upper()
        self.follow_redirects = follow_redirects
        self.user_agent = user_agent
        self.results = []
        self._lock = threading.Lock()

    def check_url(self, url: str) -> dict:
        """检查单个 URL"""
        result = {
            "url": url,
            "status": 0,
            "ok": False,
            "elapsed_ms": 0,
            "size": None,
            "content_type": None,
            "redirect_to": None,
            "error": None,
            "checked_at": datetime.now().isoformat(),
        }

        # URL 校验
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            result["error"] = f"不支持的协议: {parsed.scheme or '空'}"
            return result

        last_exception = None
        for attempt in range(self.retries + 1):
            start = time.time()
            try:
                if self.follow_redirects:
                    opener = urllib.request.build_opener(
                        urllib.request.HTTPRedirectHandler()
                    )
                else:
                    opener = urllib.request.build_opener(NoRedirectHandler())

                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": self.user_agent},
                    method=self.method,
                )

                with opener.open(req, timeout=self.timeout) as resp:
                    result["status"] = resp.status
                    result["ok"] = 200 <= resp.status < 400
                    result["content_type"] = resp.headers.get("Content-Type")
                    cl = resp.headers.get("Content-Length")
                    if cl is not None:
                        try:
                            result["size"] = int(cl)
                        except ValueError:
                            pass

                    if resp.url != url:
                        result["redirect_to"] = resp.url
                    elif 300 <= resp.status < 400:
                        # 不跟随重定向时，从 Location 头读取
                        loc = resp.headers.get("Location")
                        if loc:
                            result["redirect_to"] = loc

                    result["elapsed_ms"] = int((time.time() - start) * 1000)
                    return result

            except urllib.error.HTTPError as e:
                # HTTPError 仍是有效的响应
                result["status"] = e.code
                result["ok"] = False
                result["elapsed_ms"] = int((time.time() - start) * 1000)
                result["error"] = f"HTTP {e.code}: {e.reason}"
                if e.code in (301, 302, 303, 307, 308):
                    result["redirect_to"] = e.headers.get("Location")
                return result
            except urllib.error.URLError as e:
                last_exception = f"URL 错误: {e.reason}"
            except socket.timeout:
                last_exception = f"超时 (>{self.timeout}s)"
            except (ConnectionError, OSError) as e:
                last_exception = f"连接错误: {e}"
            except Exception as e:
                last_exception = f"{type(e).__name__}: {e}"

            if attempt < self.retries:
                time.sleep(0.3)

        result["elapsed_ms"] = int((time.time() - start) * 1000)
        result["error"] = last_exception
        return result

    def check_batch(self, urls: list, workers: int = 5, on_progress=None) -> list:
        """批量并发检查"""
        self.results.clear()
        total = len(urls)
        completed = 0

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(self.check_url, url): url for url in urls}
            for future in as_completed(futures):
                result = future.result()
                with self._lock:
                    self.results.append(result)
                    completed += 1
                if on_progress:
                    on_progress(completed, total, result)

        return self.results

    def group_by_status(self) -> dict:
        """按状态码分组"""
        groups = {k: [] for k in self.STATUS_CATEGORIES}
        for r in self.results:
            status = r["status"]
            if status == 0:
                groups["0"].append(r)
            elif 100 <= status < 200:
                groups["1xx"].append(r)
            elif 200 <= status < 300:
                groups["2xx"].append(r)
            elif 300 <= status < 400:
                groups["3xx"].append(r)
            elif 400 <= status < 500:
                groups["4xx"].append(r)
            elif 500 <= status < 600:
                groups["5xx"].append(r)
        return groups

    def summary(self) -> dict:
        """生成摘要"""
        total = len(self.results)
        ok = sum(1 for r in self.results if r["ok"])
        groups = self.group_by_status()

        elapsed = [r["elapsed_ms"] for r in self.results if r["elapsed_ms"]]
        avg_elapsed = sum(elapsed) / len(elapsed) if elapsed else 0

        return {
            "total": total,
            "ok": ok,
            "failed": total - ok,
            "by_status": {k: len(v) for k, v in groups.items()},
            "avg_elapsed_ms": int(avg_elapsed),
            "max_elapsed_ms": max(elapsed) if elapsed else 0,
            "min_elapsed_ms": min(elapsed) if elapsed else 0,
        }

    def print_report(self):
        """打印报告"""
        s = self.summary()
        print("\n" + "=" * 70)
        print("  URL 状态检查报告")
        print("=" * 70)
        print(f"总数: {s['total']}  成功: {s['ok']}  失败: {s['failed']}")
        print(
            f"平均响应: {s['avg_elapsed_ms']}ms  "
            f"最快: {s['min_elapsed_ms']}ms  最慢: {s['max_elapsed_ms']}ms"
        )

        print("\n--- 状态分布 ---")
        for cat, count in s["by_status"].items():
            if count > 0:
                desc = self.STATUS_CATEGORIES[cat]
                print(f"  {cat:4s} ({desc}): {count}")

        print("\n--- 详细结果 ---")
        # 按状态码排序
        sorted_results = sorted(
            self.results, key=lambda r: (r["status"] == 0, r["status"], r["url"])
        )
        for r in sorted_results:
            status = r["status"] if r["status"] else "ERR"
            mark = "[OK]" if r["ok"] else "[X]"
            elapsed = f"{r['elapsed_ms']:5d}ms"
            print(f"  {mark}  {str(status):4s}  {elapsed}  {r['url']}")
            if r["redirect_to"] and r["redirect_to"] != r["url"]:
                print(f"           -> 重定向: {r['redirect_to']}")
            if r["error"]:
                print(f"           错误: {r['error']}")

    def export_json(self, filepath: str):
        """导出 JSON 报告"""
        data = {
            "summary": self.summary(),
            "checked_at": datetime.now().isoformat(),
            "results": self.results,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def export_csv(self, filepath: str):
        """导出 CSV 报告"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("url,status,ok,elapsed_ms,content_type,redirect_to,error\n")
            for r in self.results:
                row = [
                    r["url"],
                    str(r["status"]),
                    "true" if r["ok"] else "false",
                    str(r["elapsed_ms"]),
                    str(r.get("content_type") or ""),
                    str(r.get("redirect_to") or ""),
                    str(r.get("error") or "").replace(",", ";"),
                ]
                f.write(",".join(f'"{v}"' for v in row) + "\n")


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """禁止重定向的 Handler"""

    def http_error_301(self, req, fp, code, msg, headers):
        return fp

    def http_error_302(self, req, fp, code, msg, headers):
        return fp

    http_error_303 = http_error_302
    http_error_307 = http_error_302
    http_error_308 = http_error_302


# ==================== 演示（离线 + 在线） ====================


def run_offline_demo(demo_dir: str):
    """离线演示：启动本地 HTTP 服务器返回多种状态码"""
    import http.server
    import socketserver
    import threading

    class TestHandler(http.server.BaseHTTPRequestHandler):
        def _route(self):
            path = self.path
            if path == "/ok":
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", "2")
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(b"OK")
            elif path == "/redirect":
                self.send_response(301)
                self.send_header("Location", "/ok")
                self.end_headers()
            elif path == "/redirect-loop":
                self.send_response(302)
                self.send_header("Location", "/redirect-loop")
                self.end_headers()
            elif path == "/notfound":
                self.send_response(404)
                self.end_headers()
            elif path == "/forbidden":
                self.send_response(403)
                self.end_headers()
            elif path == "/error":
                self.send_response(500)
                self.end_headers()
            elif path == "/slow":
                time.sleep(0.5)
                self.send_response(200)
                self.send_header("Content-Length", "4")
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(b"slow")
            elif path == "/json":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(b'{"ok": true}')
            else:
                self.send_response(404)
                self.end_headers()

        def do_GET(self):
            self._route()

        def do_HEAD(self):
            self._route()

        def log_message(self, *args, **kwargs):
            pass

    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", 0), TestHandler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    base = f"http://127.0.0.1:{port}"
    urls = [
        f"{base}/ok",
        f"{base}/redirect",
        f"{base}/notfound",
        f"{base}/forbidden",
        f"{base}/error",
        f"{base}/slow",
        f"{base}/json",
        f"{base}/nonexistent",
        "http://127.0.0.1:1/unreachable",  # 网络错误
        "ftp://example.com/x",  # 协议错误
    ]

    print(f"\n>>> 启动本地测试服务器: {base}")
    print(f">>> 检查 {len(urls)} 个 URL")

    try:
        # 1. 默认 HEAD
        checker = URLStatusChecker(
            timeout=3, retries=1, method="HEAD", follow_redirects=True
        )

        def progress(done, total, r):
            mark = "OK" if r["ok"] else "X"
            print(f"  [{done}/{total}] {mark} {r['status']:>3} {r['url']}")

        checker.check_batch(urls, workers=4, on_progress=progress)
        checker.print_report()

        # 2. 不跟随重定向
        print("\n\n>>> 不跟随重定向 (HEAD)")
        checker2 = URLStatusChecker(timeout=3, follow_redirects=False)
        checker2.check_batch(
            [f"{base}/redirect", f"{base}/ok"], workers=2
        )
        for r in checker2.results:
            print(
                f"  {r['status']}  {r['url']}  -> {r.get('redirect_to') or '无'}"
            )

        # 3. 导出报告
        json_path = os.path.join(demo_dir, "report.json")
        csv_path = os.path.join(demo_dir, "report.csv")
        checker.export_json(json_path)
        checker.export_csv(csv_path)
        print(f"\nJSON 报告: {json_path}")
        print(f"CSV 报告:  {csv_path}")

        return [json_path, csv_path]

    finally:
        httpd.shutdown()
        httpd.server_close()


def cleanup(demo_dir: str, files: list):
    for f in files:
        if f and os.path.exists(f):
            os.remove(f)


if __name__ == "__main__":
    print("=" * 70)
    print("  URL 状态检查器 Demo")
    print("=" * 70)

    demo_dir = os.path.dirname(os.path.abspath(__file__))
    generated = []
    try:
        generated = run_offline_demo(demo_dir)
    finally:
        cleanup(demo_dir, generated or [])

    print("\n" + "=" * 70)
    print("  Demo 运行完毕！")
    print("=" * 70)
