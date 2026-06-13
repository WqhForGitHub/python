"""
简单爬虫（urllib）
功能：基于 urllib 实现的网页爬虫，支持下载页面、解析链接、广度优先抓取、
      域名限制、深度限制、爬取延迟、保存到本地、提取标题/图片等
"""

import os
import re
import time
import urllib.request
import urllib.parse
import urllib.error
from html.parser import HTMLParser
from collections import deque


class LinkExtractor(HTMLParser):
    """从 HTML 中提取链接、图片、标题"""

    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.links = []
        self.images = []
        self.title = ""
        self._in_title = False
        self._title_buf = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "a" and "href" in attrs_dict:
            href = attrs_dict["href"]
            full = urllib.parse.urljoin(self.base_url, href)
            # 去除片段
            full = full.split("#")[0]
            if full.startswith(("http://", "https://")):
                self.links.append(full)
        elif tag == "img" and "src" in attrs_dict:
            src = attrs_dict["src"]
            full = urllib.parse.urljoin(self.base_url, src)
            self.images.append(full)
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
            self.title = "".join(self._title_buf).strip()

    def handle_data(self, data):
        if self._in_title:
            self._title_buf.append(data)


class SimpleCrawler:
    """简单爬虫"""

    def __init__(
        self,
        max_depth: int = 2,
        max_pages: int = 50,
        delay: float = 0.5,
        same_domain: bool = True,
        timeout: int = 10,
        user_agent: str = "Mozilla/5.0 (compatible; SimpleCrawler/1.0)",
    ):
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.delay = delay
        self.same_domain = same_domain
        self.timeout = timeout
        self.user_agent = user_agent

        self.visited = set()
        self.failed = set()
        self.results = []  # 抓取结果

    def fetch(self, url: str) -> dict:
        """抓取单个 URL"""
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                status = resp.status
                content_type = resp.headers.get("Content-Type", "")
                # 检测编码
                charset = "utf-8"
                if "charset=" in content_type:
                    charset = content_type.split("charset=")[-1].split(";")[0].strip()

                # 仅处理 HTML 与文本
                if "text" not in content_type and "html" not in content_type:
                    return {
                        "url": url,
                        "status": status,
                        "content_type": content_type,
                        "html": None,
                        "size": 0,
                    }

                data = resp.read()
                try:
                    html = data.decode(charset, errors="replace")
                except LookupError:
                    html = data.decode("utf-8", errors="replace")

                return {
                    "url": url,
                    "status": status,
                    "content_type": content_type,
                    "html": html,
                    "size": len(data),
                }
        except urllib.error.HTTPError as e:
            return {"url": url, "status": e.code, "error": f"HTTP {e.code}: {e.reason}"}
        except urllib.error.URLError as e:
            return {"url": url, "status": 0, "error": f"URL Error: {e.reason}"}
        except Exception as e:
            return {"url": url, "status": 0, "error": f"{type(e).__name__}: {e}"}

    def parse(self, url: str, html: str) -> dict:
        """解析 HTML，提取链接/图片/标题"""
        parser = LinkExtractor(url)
        try:
            parser.feed(html)
        except Exception as e:
            return {"title": "", "links": [], "images": [], "error": str(e)}

        return {
            "title": parser.title,
            "links": list(set(parser.links)),
            "images": list(set(parser.images)),
        }

    def crawl(self, start_url: str) -> list:
        """从起始 URL 开始广度优先爬取"""
        self.visited.clear()
        self.failed.clear()
        self.results.clear()

        start_domain = urllib.parse.urlparse(start_url).netloc
        queue = deque([(start_url, 0)])  # (url, depth)
        self.visited.add(start_url)

        while queue and len(self.results) < self.max_pages:
            url, depth = queue.popleft()

            # 同域限制
            if self.same_domain:
                if urllib.parse.urlparse(url).netloc != start_domain:
                    continue

            print(f"[depth={depth}] 抓取: {url}")
            result = self.fetch(url)

            if "error" in result:
                self.failed.add(url)
                print(f"  失败: {result['error']}")
                self.results.append(result)
                time.sleep(self.delay)
                continue

            # 解析
            if result.get("html"):
                parsed = self.parse(url, result["html"])
                result.update(parsed)
                print(
                    f"  标题: {parsed['title'][:50]}  "
                    f"链接数: {len(parsed['links'])}  图片数: {len(parsed['images'])}"
                )

                # 加入新链接到队列
                if depth < self.max_depth:
                    for link in parsed["links"]:
                        if link not in self.visited:
                            self.visited.add(link)
                            queue.append((link, depth + 1))

            self.results.append(result)
            time.sleep(self.delay)

        return self.results

    def save_pages(self, output_dir: str):
        """保存抓取的页面到本地"""
        os.makedirs(output_dir, exist_ok=True)
        saved = 0
        for r in self.results:
            if not r.get("html"):
                continue
            # 由 URL 生成文件名
            parsed = urllib.parse.urlparse(r["url"])
            filename = parsed.netloc + parsed.path
            filename = re.sub(r"[^\w\-_.]", "_", filename).strip("_")
            if not filename.endswith(".html"):
                filename += ".html"
            filename = filename[:200]  # 防止过长

            filepath = os.path.join(output_dir, filename)
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(r["html"])
                saved += 1
            except (IOError, OSError) as e:
                print(f"保存失败 {filename}: {e}")
        return saved

    def summary(self) -> dict:
        """生成抓取摘要"""
        success = [r for r in self.results if "error" not in r]
        total_size = sum(r.get("size", 0) for r in success)
        total_links = sum(len(r.get("links", [])) for r in success)
        total_images = sum(len(r.get("images", [])) for r in success)

        return {
            "total": len(self.results),
            "success": len(success),
            "failed": len(self.failed),
            "total_size_bytes": total_size,
            "total_links_found": total_links,
            "total_images_found": total_images,
        }

    def print_summary(self):
        """打印摘要"""
        s = self.summary()
        print("\n--- 抓取摘要 ---")
        print(f"  总页数:     {s['total']}")
        print(f"  成功:       {s['success']}")
        print(f"  失败:       {s['failed']}")
        print(f"  总大小:     {s['total_size_bytes']:,} 字节")
        print(f"  发现链接:   {s['total_links_found']}")
        print(f"  发现图片:   {s['total_images_found']}")


# ==================== 演示（离线模式） ====================


def create_demo_html_server(demo_dir: str):
    """创建一些静态 HTML 文件用于离线演示"""
    server_dir = os.path.join(demo_dir, "site")
    os.makedirs(server_dir, exist_ok=True)

    pages = {
        "index.html": """<html><head><title>首页</title></head>
<body><h1>欢迎</h1>
<a href="page1.html">页面1</a>
<a href="page2.html">页面2</a>
<a href="about.html">关于</a>
<img src="logo.png">
</body></html>""",
        "page1.html": """<html><head><title>页面1</title></head>
<body><h1>这是页面1</h1>
<a href="index.html">首页</a>
<a href="page2.html">页面2</a>
<img src="img1.jpg">
<img src="img2.jpg">
</body></html>""",
        "page2.html": """<html><head><title>页面2</title></head>
<body><h1>这是页面2</h1>
<a href="page1.html">页面1</a>
<a href="about.html">关于</a>
</body></html>""",
        "about.html": """<html><head><title>关于</title></head>
<body><h1>关于我们</h1>
<a href="index.html">返回首页</a>
</body></html>""",
    }

    for name, content in pages.items():
        with open(os.path.join(server_dir, name), "w", encoding="utf-8") as f:
            f.write(content)

    return server_dir


def cleanup_demo(demo_dir: str):
    """清理"""
    import shutil

    for sub in ["site", "downloaded"]:
        p = os.path.join(demo_dir, sub)
        if os.path.exists(p):
            shutil.rmtree(p, ignore_errors=True)


def run_offline_demo(demo_dir: str):
    """离线演示：使用本地 HTTP 服务"""
    import http.server
    import socketserver
    import threading

    server_dir = create_demo_html_server(demo_dir)

    # 启动本地 HTTP 服务器
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=server_dir, **kwargs)

        def log_message(self, *args, **kwargs):
            pass  # 静默

    # 找空闲端口
    httpd = socketserver.TCPServer(("127.0.0.1", 0), Handler)
    port = httpd.server_address[1]

    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    try:
        start_url = f"http://127.0.0.1:{port}/index.html"
        print(f"\n>>> 离线演示，启动本地服务器: http://127.0.0.1:{port}/")

        crawler = SimpleCrawler(
            max_depth=2, max_pages=10, delay=0.1, same_domain=True, timeout=5
        )
        crawler.crawl(start_url)
        crawler.print_summary()

        # 保存
        out_dir = os.path.join(demo_dir, "downloaded")
        saved = crawler.save_pages(out_dir)
        print(f"\n已保存 {saved} 个页面到 {out_dir}")

        # 解析单个 URL
        print("\n>>> 单页解析示例")
        single = crawler.fetch(start_url)
        if "html" in single and single["html"]:
            parsed = crawler.parse(start_url, single["html"])
            print(f"  标题: {parsed['title']}")
            print(f"  链接: {parsed['links']}")
            print(f"  图片: {parsed['images']}")

    finally:
        httpd.shutdown()
        httpd.server_close()


if __name__ == "__main__":
    print("=" * 60)
    print("  简单爬虫（urllib）Demo")
    print("=" * 60)

    demo_dir = os.path.dirname(os.path.abspath(__file__))

    try:
        run_offline_demo(demo_dir)
    finally:
        cleanup_demo(demo_dir)

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
