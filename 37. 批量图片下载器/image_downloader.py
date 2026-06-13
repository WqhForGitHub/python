"""
批量图片下载器
功能：批量下载图片到本地，支持从 URL 列表、HTML 页面、并发下载、
      失败重试、进度显示、文件去重、按尺寸/扩展名过滤、本地缓存等
"""

import os
import re
import time
import hashlib
import urllib.request
import urllib.parse
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser


class ImageURLExtractor(HTMLParser):
    """从 HTML 中提取图片 URL"""

    def __init__(self, base_url: str = ""):
        super().__init__()
        self.base_url = base_url
        self.images = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "img":
            src = attrs_dict.get("src") or attrs_dict.get("data-src")
            if src:
                self.images.append(self._normalize(src))
            srcset = attrs_dict.get("srcset")
            if srcset:
                # srcset 可能为 "url1 1x, url2 2x"
                for part in srcset.split(","):
                    url = part.strip().split()[0]
                    if url:
                        self.images.append(self._normalize(url))
        elif tag in ("a", "source"):
            href = attrs_dict.get("href") or attrs_dict.get("src")
            if href and self._looks_like_image(href):
                self.images.append(self._normalize(href))

    def _normalize(self, url: str) -> str:
        if self.base_url:
            return urllib.parse.urljoin(self.base_url, url)
        return url

    @staticmethod
    def _looks_like_image(url: str) -> bool:
        ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower()
        return ext in {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"}


class ImageDownloader:
    """批量图片下载器"""

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        ),
        "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
    }

    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
                        ".svg", ".ico", ".tiff"}

    def __init__(self, save_dir: str = "downloads",
                 max_workers: int = 5,
                 timeout: int = 15,
                 max_retries: int = 3,
                 headers: dict = None):
        self.save_dir = save_dir
        self.max_workers = max_workers
        self.timeout = timeout
        self.max_retries = max_retries
        self.headers = headers or dict(self.DEFAULT_HEADERS)

        # 统计
        self.success_count = 0
        self.fail_count = 0
        self.skip_count = 0
        self.total_bytes = 0
        # 已下载的 hash，用于去重
        self.downloaded_hashes = set()
        # 失败列表
        self.failed_urls = []

        os.makedirs(save_dir, exist_ok=True)

    # ==================== URL 收集 ====================

    def extract_urls_from_html(self, html: str, base_url: str = "") -> list:
        """从 HTML 字符串提取图片 URL"""
        parser = ImageURLExtractor(base_url)
        parser.feed(html)
        # 去重保持顺序
        seen = set()
        urls = []
        for u in parser.images:
            if u not in seen:
                seen.add(u)
                urls.append(u)
        return urls

    def extract_urls_from_page(self, page_url: str) -> list:
        """从在线页面提取图片 URL"""
        try:
            req = urllib.request.Request(page_url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                charset = resp.headers.get_content_charset() or "utf-8"
                html = resp.read().decode(charset, errors="replace")
            return self.extract_urls_from_html(html, page_url)
        except (urllib.error.URLError, ValueError) as e:
            print(f"[错误] 无法获取页面 {page_url}: {e}")
            return []

    # ==================== 下载 ====================

    def download_one(self, url: str, filename: str = None,
                    overwrite: bool = False) -> dict:
        """下载单张图片
        返回: {"url", "path", "status", "size", "message"}
        """
        result = {"url": url, "path": None, "status": "fail",
                  "size": 0, "message": ""}

        # 生成文件名
        if not filename:
            filename = self._gen_filename(url)
        path = os.path.join(self.save_dir, filename)

        # 跳过已存在
        if os.path.exists(path) and not overwrite:
            result["status"] = "skip"
            result["path"] = path
            result["size"] = os.path.getsize(path)
            result["message"] = "文件已存在"
            return result

        last_err = None
        for attempt in range(1, self.max_retries + 1):
            try:
                req = urllib.request.Request(url, headers=self.headers)
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    data = resp.read()
                    content_type = resp.headers.get("Content-Type", "")

                # 内容去重
                digest = hashlib.md5(data).hexdigest()
                if digest in self.downloaded_hashes:
                    result["status"] = "skip"
                    result["message"] = "内容重复，已跳过"
                    return result

                # 修正扩展名
                if not os.path.splitext(filename)[1]:
                    ext = self._ext_from_content_type(content_type) or ".jpg"
                    filename += ext
                    path = os.path.join(self.save_dir, filename)

                with open(path, "wb") as f:
                    f.write(data)

                self.downloaded_hashes.add(digest)
                result.update({
                    "status": "success",
                    "path": path,
                    "size": len(data),
                    "message": f"下载成功 (尝试 {attempt})",
                })
                return result
            except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
                last_err = str(e)
                if attempt < self.max_retries:
                    time.sleep(0.5 * attempt)

        result["message"] = f"重试 {self.max_retries} 次后仍失败: {last_err}"
        return result

    def download_batch(self, urls: list, show_progress: bool = True) -> list:
        """批量并发下载"""
        self.success_count = 0
        self.fail_count = 0
        self.skip_count = 0
        self.total_bytes = 0
        self.failed_urls = []

        results = []
        total = len(urls)
        if total == 0:
            return results

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.download_one, url): url
                      for url in urls}

            for i, future in enumerate(as_completed(futures), 1):
                url = futures[future]
                try:
                    result = future.result()
                except Exception as e:
                    result = {"url": url, "status": "fail",
                             "size": 0, "message": str(e)}

                results.append(result)
                self._update_stats(result)

                if show_progress:
                    self._print_progress(i, total, result)

        return results

    def _update_stats(self, result: dict):
        if result["status"] == "success":
            self.success_count += 1
            self.total_bytes += result["size"]
        elif result["status"] == "skip":
            self.skip_count += 1
        else:
            self.fail_count += 1
            self.failed_urls.append(result["url"])

    def _print_progress(self, current: int, total: int, result: dict):
        percent = current * 100 // total
        status_icon = {"success": "[OK]", "skip": "[--]", "fail": "[XX]"}
        icon = status_icon.get(result["status"], "[??]")
        url = result["url"]
        if len(url) > 50:
            url = url[:25] + "..." + url[-22:]
        print(f"  {icon} [{current:>3}/{total}] {percent:>3}%  {url}")

    # ==================== 工具方法 ====================

    @staticmethod
    def _gen_filename(url: str) -> str:
        """根据 URL 生成本地文件名"""
        parsed = urllib.parse.urlparse(url)
        name = os.path.basename(parsed.path) or "image"
        # 清理非法字符
        name = re.sub(r'[<>:"/\\|?*]', "_", name)
        # 如果太长或没有扩展名，使用 URL 哈希
        if len(name) > 100 or not os.path.splitext(name)[1]:
            digest = hashlib.md5(url.encode()).hexdigest()[:10]
            ext = os.path.splitext(name)[1] or ""
            name = f"img_{digest}{ext}"
        return name

    @staticmethod
    def _ext_from_content_type(ct: str) -> str:
        """从 Content-Type 推断扩展名"""
        ct = ct.lower().split(";")[0].strip()
        mapping = {
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "image/bmp": ".bmp",
            "image/svg+xml": ".svg",
        }
        return mapping.get(ct, "")

    def filter_by_extension(self, urls: list, extensions: list = None) -> list:
        """按扩展名过滤 URL"""
        exts = set(e.lower() for e in (extensions or self.IMAGE_EXTENSIONS))
        result = []
        for u in urls:
            ext = os.path.splitext(urllib.parse.urlparse(u).path)[1].lower()
            if ext in exts:
                result.append(u)
        return result

    def print_summary(self):
        """打印下载摘要"""
        total = self.success_count + self.fail_count + self.skip_count
        print(f"\n--- 下载摘要 ---")
        print(f"总计:    {total}")
        print(f"成功:    {self.success_count}")
        print(f"跳过:    {self.skip_count}")
        print(f"失败:    {self.fail_count}")
        print(f"总下载量: {self._format_size(self.total_bytes)}")
        if self.failed_urls:
            print(f"失败 URL ({len(self.failed_urls)}):")
            for u in self.failed_urls[:5]:
                print(f"  - {u}")
            if len(self.failed_urls) > 5:
                print(f"  ... 以及 {len(self.failed_urls) - 5} 个其他")

    @staticmethod
    def _format_size(size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"


# ==================== 演示（离线模拟） ====================

class MockResponse:
    """模拟 urlopen 返回的响应对象"""

    def __init__(self, data: bytes, content_type: str = "image/png"):
        self.data = data
        self._headers = {"Content-Type": content_type}

    def read(self):
        return self.data

    @property
    def headers(self):
        class H:
            def __init__(self, hd):
                self.hd = hd

            def get(self, k, default=""):
                return self.hd.get(k, default)

            def get_content_charset(self):
                return "utf-8"

        return H(self._headers)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def mock_urlopen(req, timeout=None):
    """模拟 urlopen，根据 URL 返回不同的内容"""
    url = req.full_url if hasattr(req, "full_url") else str(req)
    # 模拟特定 URL 失败
    if "fail" in url:
        raise urllib.error.URLError("模拟网络错误")
    # 根据 URL 末尾生成不同的"图片"内容
    if url.endswith(".png"):
        data = b"\x89PNG\r\n\x1a\n" + url.encode() * 50
        return MockResponse(data, "image/png")
    if url.endswith(".jpg") or url.endswith(".jpeg"):
        data = b"\xff\xd8\xff" + url.encode() * 80
        return MockResponse(data, "image/jpeg")
    if url.endswith(".gif"):
        return MockResponse(b"GIF89a" + url.encode() * 30, "image/gif")
    # 模拟 HTML 页面
    if url.endswith(".html") or url.endswith("/"):
        html = f"""
        <html><body>
            <h1>测试图集</h1>
            <img src="/img/photo1.jpg" alt="p1">
            <img src="/img/photo2.png" data-src="/img/photo2_lazy.png">
            <img src="https://cdn.example.com/big.jpeg">
            <a href="/gallery/full/img.png">点击</a>
            <img src="/img/anim.gif">
            <img src="/img/photo1.jpg">  <!-- 重复 -->
        </body></html>
        """.encode("utf-8")
        return MockResponse(html, "text/html")
    return MockResponse(b"BIN" + url.encode() * 10, "application/octet-stream")


if __name__ == "__main__":
    print("=" * 60)
    print("  批量图片下载器 Demo")
    print("=" * 60)
    print("注：本 Demo 使用模拟 urlopen，离线即可运行")

    # 替换 urllib.request.urlopen 为模拟版本
    urllib.request.urlopen = mock_urlopen

    base_dir = os.path.dirname(__file__)
    save_dir = os.path.join(base_dir, "downloads")

    # 1. 从 HTML 字符串提取 URL
    print("\n--- 1. 从 HTML 中提取图片 URL ---")
    html = """
    <html><body>
        <img src="/static/a.jpg">
        <img src="/static/b.png" data-src="/static/b_hd.png">
        <img srcset="/static/c.jpg 1x, /static/c@2x.jpg 2x">
        <a href="/full/d.gif">全图</a>
    </body></html>
    """
    downloader = ImageDownloader(save_dir=save_dir, max_workers=3, max_retries=2)
    urls = downloader.extract_urls_from_html(html, base_url="https://example.com/")
    for u in urls:
        print(f"  发现: {u}")

    # 2. 从在线页面提取（使用模拟）
    print("\n--- 2. 从页面提取并过滤 ---")
    page_urls = downloader.extract_urls_from_page("https://example.com/index.html")
    for u in page_urls:
        print(f"  发现: {u}")
    filtered = downloader.filter_by_extension(page_urls, [".jpg", ".png"])
    print(f"过滤后（仅 jpg/png）: {len(filtered)} 个")

    # 3. 单张下载
    print("\n--- 3. 单张图片下载 ---")
    result = downloader.download_one("https://example.com/test.png")
    print(f"  状态: {result['status']}, 大小: {result['size']} 字节")
    print(f"  路径: {result['path']}")
    print(f"  消息: {result['message']}")

    # 4. 批量下载
    print("\n--- 4. 批量并发下载 ---")
    test_urls = [
        "https://example.com/img1.jpg",
        "https://example.com/img2.png",
        "https://example.com/img3.gif",
        "https://example.com/img4.jpeg",
        "https://example.com/img5.png",
        "https://example.com/img1.jpg",       # 重复 URL
        "https://example.com/fail/bad.png",   # 模拟失败
        "https://example.com/img6.png",
    ]
    results = downloader.download_batch(test_urls, show_progress=True)
    downloader.print_summary()

    # 5. 失败重试演示
    print("\n--- 5. 失败 URL 列表 ---")
    for u in downloader.failed_urls:
        print(f"  - {u}")

    # 6. 二次下载（演示去重/跳过已存在）
    print("\n--- 6. 二次运行（演示跳过已存在） ---")
    results = downloader.download_batch(
        ["https://example.com/img1.jpg", "https://example.com/img2.png"],
        show_progress=True,
    )
    downloader.print_summary()

    # 7. 查看保存目录
    print("\n--- 7. 下载目录内容 ---")
    if os.path.exists(save_dir):
        files = sorted(os.listdir(save_dir))
        print(f"  共 {len(files)} 个文件:")
        for f in files:
            size = os.path.getsize(os.path.join(save_dir, f))
            print(f"    - {f} ({size} 字节)")

    # 清理
    import shutil
    if os.path.exists(save_dir):
        shutil.rmtree(save_dir)

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
    print("\n实际使用提示：")
    print("  downloader = ImageDownloader(save_dir='./pics', max_workers=10)")
    print("  urls = downloader.extract_urls_from_page('https://your-site.com')")
    print("  downloader.download_batch(urls)")
    print("  downloader.print_summary()")
