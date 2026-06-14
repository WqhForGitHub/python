"""
URL 状态检查器
功能：
    - 批量检查 URL 状态码（HEAD 优先，回退 GET）
    - 测量响应耗时
    - 自动跟随重定向并记录跳转链
    - 支持并发检查（线程池）
    - 输出汇总报告（成功/失败/超时分类）
    - 保存结果到 CSV / JSON
"""

import os
import csv
import json
import time
import urllib.request
import urllib.parse
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed


USER_AGENT = "URLStatusChecker/1.0 (+https://example.com)"


class URLStatusChecker:
    """URL 状态检查器"""

    def __init__(self, timeout=8, max_workers=5, follow_redirects=True):
        self.timeout = timeout
        self.max_workers = max_workers
        self.follow_redirects = follow_redirects

    # -------- 单 URL 检查 --------
    def check(self, url: str) -> dict:
        """检查单个 URL"""
        result = {
            "url": url,
            "status": 0,
            "ok": False,
            "elapsed_ms": 0,
            "final_url": url,
            "redirects": [],
            "method": "HEAD",
            "content_type": "",
            "size": 0,
            "error": "",
        }

        if not self._is_valid_url(url):
            result["error"] = "Invalid URL"
            return result

        start = time.time()
        try:
            # 先 HEAD
            status, headers, final_url, redirects = self._request(url, method="HEAD")
            if status in (405, 501) or status == 0:
                # 部分服务器不支持 HEAD，回退 GET
                result["method"] = "GET"
                status, headers, final_url, redirects = self._request(
                    url, method="GET", read_body=True
                )
            result["status"] = status
            result["final_url"] = final_url
            result["redirects"] = redirects
            result["ok"] = 200 <= status < 400
            if headers:
                result["content_type"] = headers.get("Content-Type", "")
                cl = headers.get("Content-Length")
                if cl and cl.isdigit():
                    result["size"] = int(cl)
        except urllib.error.HTTPError as e:
            result["status"] = e.code
            result["error"] = str(e)
        except urllib.error.URLError as e:
            result["error"] = f"URLError: {e.reason}"
        except TimeoutError:
            result["error"] = "Timeout"
        except Exception as e:
            result["error"] = type(e).__name__ + ": " + str(e)
        finally:
            result["elapsed_ms"] = int((time.time() - start) * 1000)

        return result

    def _request(self, url, method="HEAD", read_body=False):
        """发送 HTTP 请求并跟踪重定向"""
        redirects = []
        current = url
        final_url = url
        status = 0
        headers = None

        # 自定义 opener，禁用自动重定向以记录跳转链
        opener = urllib.request.build_opener(_NoRedirectHandler())

        for _ in range(10):  # 最多 10 跳
            req = urllib.request.Request(
                current,
                method=method,
                headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
            )
            try:
                resp = opener.open(req, timeout=self.timeout)
                status = resp.status
                headers = resp.headers
                final_url = current
                if read_body:
                    resp.read(1024)  # 仅读一小段
                resp.close()
                break
            except urllib.error.HTTPError as e:
                status = e.code
                headers = e.headers
                if self.follow_redirects and 300 <= status < 400:
                    location = e.headers.get("Location")
                    if not location:
                        break
                    location = urllib.parse.urljoin(current, location)
                    redirects.append((current, status, location))
                    current = location
                    final_url = location
                    continue
                else:
                    final_url = current
                    break

        return status, headers, final_url, redirects

    def _is_valid_url(self, url: str) -> bool:
        try:
            parsed = urllib.parse.urlparse(url)
            return parsed.scheme in ("http", "https") and bool(parsed.netloc)
        except Exception:
            return False

    # -------- 批量检查 --------
    def check_many(self, urls: list, on_progress=None) -> list:
        """并发检查多个 URL"""
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            future_map = {pool.submit(self.check, u): u for u in urls}
            for i, fut in enumerate(as_completed(future_map), 1):
                r = fut.result()
                results.append(r)
                if on_progress:
                    on_progress(i, len(urls), r)
        # 保持原顺序
        order = {u: i for i, u in enumerate(urls)}
        results.sort(key=lambda x: order.get(x["url"], 1e9))
        return results

    # -------- 报告 / 导出 --------
    def summary(self, results: list) -> dict:
        ok = sum(1 for r in results if r["ok"])
        fail = sum(1 for r in results if not r["ok"] and not r["error"])
        err = sum(1 for r in results if r["error"])
        avg_ms = (
            int(sum(r["elapsed_ms"] for r in results) / len(results)) if results else 0
        )
        by_status = {}
        for r in results:
            by_status[r["status"]] = by_status.get(r["status"], 0) + 1
        return {
            "total": len(results),
            "ok": ok,
            "fail": fail,
            "error": err,
            "avg_ms": avg_ms,
            "by_status": by_status,
        }

    def print_report(self, results: list):
        print(
            f"{'状态':<6}{'耗时(ms)':<10}{'方法':<6}{'重定向':<6}{'URL':<50}  备注"
        )
        print("-" * 100)
        for r in results:
            status = str(r["status"]) if r["status"] else "ERR"
            note = r["error"] if r["error"] else r["content_type"]
            print(
                f"{status:<6}{r['elapsed_ms']:<10}{r['method']:<6}"
                f"{len(r['redirects']):<6}{r['url'][:48]:<50}  {note[:30]}"
            )
            for src, code, dst in r["redirects"]:
                print(f"      └─ {code} -> {dst}")

        s = self.summary(results)
        print("\n--- 汇总 ---")
        print(f"  总数: {s['total']}  正常: {s['ok']}  失败: {s['fail']}  错误: {s['error']}")
        print(f"  平均耗时: {s['avg_ms']} ms")
        print(f"  状态码分布: {s['by_status']}")

    def export_csv(self, results: list, filepath: str):
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(
                ["url", "status", "ok", "elapsed_ms", "final_url", "redirects", "error"]
            )
            for r in results:
                w.writerow(
                    [
                        r["url"],
                        r["status"],
                        r["ok"],
                        r["elapsed_ms"],
                        r["final_url"],
                        len(r["redirects"]),
                        r["error"],
                    ]
                )

    def export_json(self, results: list, filepath: str):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """禁止 urllib 自动重定向"""

    def http_error_301(self, req, fp, code, msg, headers):
        raise urllib.error.HTTPError(req.full_url, code, msg, headers, fp)

    http_error_302 = http_error_301
    http_error_303 = http_error_301
    http_error_307 = http_error_301
    http_error_308 = http_error_301


# ==================== Demo ====================

if __name__ == "__main__":
    print("=" * 60)
    print("  URL 状态检查器 Demo")
    print("=" * 60)

    urls = [
        "http://example.com",
        "https://www.python.org",
        "http://httpbin.org/status/200",
        "http://httpbin.org/status/404",
        "http://httpbin.org/status/500",
        "http://httpbin.org/redirect/2",
        "http://nonexistent-domain-xxxx-test.invalid",
        "not_a_url",
        "https://www.google.com",
    ]

    checker = URLStatusChecker(timeout=6, max_workers=4)

    print("\n--- 1. 单 URL 检查 ---")
    r = checker.check("http://example.com")
    for k, v in r.items():
        print(f"  {k:<14} = {v}")

    print("\n--- 2. 批量并发检查 ---")

    def progress(i, total, r):
        flag = "OK " if r["ok"] else "ERR"
        print(f"  [{i}/{total}] {flag} {r['status']:<4} {r['url']}")

    try:
        results = checker.check_many(urls, on_progress=progress)
    except Exception as e:
        print(f"  网络错误（离线环境正常）: {e}")
        results = []

    print("\n--- 3. 报告 ---")
    checker.print_report(results)

    # 导出
    if results:
        out_csv = os.path.join(os.path.dirname(__file__), "url_status.csv")
        out_json = os.path.join(os.path.dirname(__file__), "url_status.json")
        checker.export_csv(results, out_csv)
        checker.export_json(results, out_json)
        print(f"\n结果已导出: {out_csv}")
        print(f"             {out_json}")
        # 清理
        os.remove(out_csv)
        os.remove(out_json)

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
