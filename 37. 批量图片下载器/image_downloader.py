"""
批量图片下载器
功能：
    - 从给定的图片 URL 列表批量下载
    - 支持自定义保存目录、文件命名规则
    - 自动跳过已存在的文件（断点续传简化版）
    - 支持并发下载（线程池）
    - 支持失败重试与超时控制
    - 显示进度与统计信息
    - 由于演示环境无法联网，main 中以 Mock(本地 HTTP 模拟) 方式演示
"""

import os
import re
import time
import urllib.request
import urllib.error
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed


class ImageDownloader:
    """图片批量下载器"""

    def __init__(
        self,
        save_dir: str,
        timeout: int = 10,
        max_retries: int = 3,
        max_workers: int = 4,
        user_agent: str = "Mozilla/5.0 (image-downloader)",
        opener=None,
    ):
        self.save_dir = save_dir
        self.timeout = timeout
        self.max_retries = max_retries
        self.max_workers = max_workers
        self.user_agent = user_agent
        # 允许注入 opener (便于测试)
        self.opener = opener or urllib.request.build_opener()
        os.makedirs(self.save_dir, exist_ok=True)

    # -------- 工具方法 --------
    @staticmethod
    def _safe_filename(name: str) -> str:
        """清理非法字符"""
        name = re.sub(r'[\\/:*?"<>|]', "_", name)
        return name.strip() or "image"

    def _filename_from_url(self, url: str, idx: int) -> str:
        path = urllib.parse.urlparse(url).path
        fname = os.path.basename(path) or f"image_{idx}.jpg"
        # 没有扩展名则默认 jpg
        if not os.path.splitext(fname)[1]:
            fname += ".jpg"
        return self._safe_filename(fname)

    # -------- 单文件下载 --------
    def download_one(self, url: str, idx: int = 0, filename: str = None) -> dict:
        fname = filename or self._filename_from_url(url, idx)
        path = os.path.join(self.save_dir, fname)

        if os.path.isfile(path) and os.path.getsize(path) > 0:
            return {"url": url, "path": path, "status": "skipped", "size": os.path.getsize(path)}

        last_err = None
        for attempt in range(1, self.max_retries + 1):
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": self.user_agent}
                )
                with self.opener.open(req, timeout=self.timeout) as resp:
                    data = resp.read()
                with open(path, "wb") as f:
                    f.write(data)
                return {
                    "url": url,
                    "path": path,
                    "status": "ok",
                    "size": len(data),
                    "attempt": attempt,
                }
            except (urllib.error.URLError, OSError, TimeoutError) as e:
                last_err = e
                time.sleep(0.2 * attempt)
        return {
            "url": url,
            "path": path,
            "status": "failed",
            "error": str(last_err),
        }

    # -------- 批量下载 --------
    def download_all(self, urls: list, concurrent: bool = True) -> dict:
        results = []
        if concurrent and self.max_workers > 1:
            with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
                futs = {
                    ex.submit(self.download_one, url, i): (i, url)
                    for i, url in enumerate(urls)
                }
                for fut in as_completed(futs):
                    results.append(fut.result())
        else:
            for i, url in enumerate(urls):
                results.append(self.download_one(url, i))

        ok = sum(1 for r in results if r["status"] == "ok")
        skipped = sum(1 for r in results if r["status"] == "skipped")
        failed = sum(1 for r in results if r["status"] == "failed")
        total_size = sum(r.get("size", 0) for r in results if r["status"] != "failed")

        return {
            "total": len(urls),
            "ok": ok,
            "skipped": skipped,
            "failed": failed,
            "size_bytes": total_size,
            "results": results,
        }


# ==================== Demo ====================

import io
import shutil
import http.server
import socketserver
import threading


def _start_mock_server(directory: str):
    """启动本地 HTTP 服务，返回 (server, port)"""
    handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(
        *a, directory=directory, **kw
    )
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd, port


def _make_fake_image(path: str, color_byte: int = 0xFF, size: int = 256):
    """生成一个伪造的二进制 '图片' 文件"""
    data = bytes([color_byte]) * size
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


if __name__ == "__main__":
    print("=" * 60)
    print("  批量图片下载器 Demo")
    print("=" * 60)

    base = os.path.dirname(os.path.abspath(__file__))
    serve_dir = os.path.join(base, "_serve")
    save_dir = os.path.join(base, "downloads")
    for d in (serve_dir, save_dir):
        if os.path.exists(d):
            shutil.rmtree(d)
        os.makedirs(d)

    # 准备 5 张假图片
    fake_images = ["a.jpg", "b.png", "c.gif", "sub/d.jpeg", "broken.jpg"]
    for fn in fake_images[:-1]:
        _make_fake_image(os.path.join(serve_dir, fn), size=512 + len(fn) * 100)
    # broken.jpg 不创建，下载会 404

    # 启动本地 HTTP 模拟服务
    httpd, port = _start_mock_server(serve_dir)
    base_url = f"http://127.0.0.1:{port}"
    print(f"\n  本地 Mock 服务: {base_url}")

    urls = [f"{base_url}/{fn}" for fn in fake_images]

    downloader = ImageDownloader(save_dir, max_workers=3, max_retries=2, timeout=5)

    print("\n--- 第 1 次批量下载 ---")
    res = downloader.download_all(urls)
    print(f"  总数: {res['total']}, 成功: {res['ok']}, 失败: {res['failed']}, 跳过: {res['skipped']}")
    print(f"  下载大小: {res['size_bytes']} bytes")
    for r in res["results"]:
        if r["status"] == "ok":
            print(f"  [OK]   {os.path.basename(r['path'])}  ({r['size']} bytes)")
        elif r["status"] == "skipped":
            print(f"  [SKIP] {os.path.basename(r['path'])}")
        else:
            print(f"  [FAIL] {r['url']}  -> {r.get('error','')[:50]}")

    print("\n--- 第 2 次（应全部跳过） ---")
    res2 = downloader.download_all(urls)
    print(f"  跳过 {res2['skipped']} / 总 {res2['total']}")

    httpd.shutdown()

    # 列出下载目录
    print("\n--- 下载目录内容 ---")
    for fn in sorted(os.listdir(save_dir)):
        size = os.path.getsize(os.path.join(save_dir, fn))
        print(f"  {fn:<20} {size} bytes")

    # 清理
    shutil.rmtree(serve_dir, ignore_errors=True)
    shutil.rmtree(save_dir, ignore_errors=True)

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
