"""
简单爬虫（urllib）
功能：
    - 基于 urllib 抓取网页
    - 解析 <title>、<meta>、链接、图片
    - 自动处理编码、重定向、超时
    - 支持广度优先递归抓取（限定域名 + 最大深度 + 数量）
    - 保存抓取结果到本地（HTML / 摘要 JSON）

注意：本 demo 默认使用本地内置 HTML 字符串模拟网页（不依赖外网），
      也可手动传入真实 URL 调用 fetch() 进行抓取。
"""

import os
import re
import json
import gzip
import io
import urllib.request
import urllib.parse
import urllib.error
from html.parser import HTMLParser
from collections import deque


USER_AGENT = "Mozilla/5.0 (compatible; SimpleCrawler/1.0; +https://example.com/bot)"


class _LinkParser(HTMLParser):
    """解析 HTML 提取信息"""

    def __init__(self, base_url=""):
        super().__init__()
        self.base_url = base_url
        self.title = ""
        self._in_title = False
        self.metas = {}
        self.links = []
        self.images = []
        self.text_chunks = []
        self._skip_data = False

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            name = attr.get("name") or attr.get("property") or ""
            content = attr.get("content", "")
            if name:
                self.metas[name.lower()] = content
        elif tag == "a" and "href" in attr:
            href = self._absolute(attr["href"])
            if href:
                self.links.append(href)
        elif tag == "img" and "src" in attr:
            src = self._absolute(attr["src"])
            if src:
                self.images.append(src)
        elif tag in ("script", "style"):
            self._skip_data = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag in ("script", "style"):
            self._skip_data = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif not self._skip_data:
            text = data.strip()
            if text:
                self.text_chunks.append(text)

    def _absolute(self, url):
        if not url or url.startswith(("javascript:", "mailto:", "#")):
            return None
        if self.base_url:
            return urllib.parse.urljoin(self.base_url, url)
        return url


class SimpleCrawler:
    """简单爬虫"""

    def __init__(self, timeout=10, max_pages=20, max_depth=2, same_domain=True):
        self.timeout = timeout
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.same_domain = same_domain
        self.visited = set()
        self.results = []

    # -------- 单页抓取 --------
    def fetch(self, url: str) -> dict:
        """抓取单个 URL，返回 {url, status, content, headers}"""
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Encoding": "gzip",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                content = self._decode(raw, resp.headers.get("Content-Type", ""))
                return {
                    "url": resp.geturl(),
                    "status": resp.status,
                    "content": content,
                    "headers": dict(resp.headers),
                }
        except urllib.error.HTTPError as e:
            return {"url": url, "status": e.code, "content": "", "error": str(e)}
        except urllib.error.URLError as e:
            return {"url": url, "status": 0, "content": "", "error": str(e.reason)}
        except Exception as e:
            return {"url": url, "status": -1, "content": "", "error": str(e)}

    def _decode(self, raw: bytes, content_type: str) -> str:
        """根据 Content-Type 或 meta 解码"""
        # 优先使用 Content-Type charset
        m = re.search(r"charset=([\w\-]+)", content_type, re.I)
        if m:
            try:
                return raw.decode(m.group(1), errors="replace")
            except LookupError:
                pass
        # 尝试常用编码
        for enc in ("utf-8", "gbk", "latin-1"):
            try:
                return raw.decode(enc)
            except UnicodeDecodeError:
                continue
        return raw.decode("utf-8", errors="replace")

    # -------- 解析 --------
    def parse(self, html: str, base_url: str = "") -> dict:
        """解析 HTML，返回结构化数据"""
        parser = _LinkParser(base_url=base_url)
        try:
            parser.feed(html)
        except Exception:
            pass
        return {
            "title": parser.title.strip(),
            "metas": parser.metas,
            "links": list(dict.fromkeys(parser.links)),  # 去重保序
            "images": list(dict.fromkeys(parser.images)),
            "text": " ".join(parser.text_chunks)[:500],
        }

    # -------- 广度优先递归 --------
    def crawl(self, start_url: str) -> list:
        """从 start_url 开始爬取"""
        self.visited.clear()
        self.results.clear()

        domain = urllib.parse.urlparse(start_url).netloc
        queue = deque([(start_url, 0)])

        while queue and len(self.results) < self.max_pages:
            url, depth = queue.popleft()
            if url in self.visited:
                continue
            self.visited.add(url)

            print(f"  [深度 {depth}] 抓取: {url}")
            page = self.fetch(url)
            parsed = self.parse(page.get("content", ""), base_url=url)

            self.results.append(
                {
                    "url": page["url"],
                    "status": page["status"],
                    "depth": depth,
                    "title": parsed["title"],
                    "links_count": len(parsed["links"]),
                    "images_count": len(parsed["images"]),
                    "preview": parsed["text"][:120],
                }
            )

            if depth < self.max_depth:
                for link in parsed["links"]:
                    if link in self.visited:
                        continue
                    if self.same_domain:
                        if urllib.parse.urlparse(link).netloc != domain:
                            continue
                    queue.append((link, depth + 1))

        return self.results

    def save_results(self, filepath: str):
        """保存抓取摘要到 JSON"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)


# ==================== Demo ====================


SAMPLE_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="description" content="一个简单的爬虫演示页面">
<meta name="keywords" content="python,crawler,urllib,demo">
<meta property="og:title" content="演示首页">
<title>简单爬虫 Demo - 首页</title>
</head>
<body>
<h1>欢迎来到 Demo 首页</h1>
<p>这是一个用于演示 <b>urllib 爬虫</b> 的静态页面。</p>
<ul>
    <li><a href="/about">关于我们</a></li>
    <li><a href="/products">产品列表</a></li>
    <li><a href="https://www.python.org/" rel="external">Python 官网</a></li>
    <li><a href="javascript:void(0)">JS 链接</a></li>
    <li><a href="mailto:test@example.com">邮件链接</a></li>
</ul>
<img src="/static/logo.png" alt="logo">
<img src="https://example.com/banner.jpg">
<script>console.log('忽略脚本内容');</script>
</body>
</html>
"""


if __name__ == "__main__":
    print("=" * 60)
    print("  简单爬虫（urllib）Demo")
    print("=" * 60)

    crawler = SimpleCrawler(timeout=5, max_pages=5, max_depth=1)

    # 1. 解析本地 HTML
    print("\n--- 1. 解析示例 HTML ---")
    parsed = crawler.parse(SAMPLE_HTML, base_url="https://demo.local/")
    print(f"标题:     {parsed['title']}")
    print(f"meta 标签:")
    for k, v in parsed["metas"].items():
        print(f"  {k:<20} = {v}")
    print(f"链接 ({len(parsed['links'])}):")
    for u in parsed["links"]:
        print(f"  -> {u}")
    print(f"图片 ({len(parsed['images'])}):")
    for u in parsed["images"]:
        print(f"  -> {u}")
    print(f"正文预览: {parsed['text'][:80]}...")

    # 2. 抓取真实 URL（如能联网）
    print("\n--- 2. 尝试抓取 http://example.com ---")
    try:
        page = crawler.fetch("http://example.com")
        if page["status"] == 200:
            res = crawler.parse(page["content"], base_url=page["url"])
            print(f"  状态码: {page['status']}")
            print(f"  标题:   {res['title']}")
            print(f"  链接数: {len(res['links'])}")
        else:
            print(f"  状态码: {page['status']}  错误: {page.get('error', '')}")
    except Exception as e:
        print(f"  无法访问网络: {e}")

    # 3. 演示广度爬取（仅在有网络时）
    print("\n--- 3. 广度优先爬取 (max_pages=3, depth=1) ---")
    try:
        results = crawler.crawl("http://example.com")
        for r in results:
            print(f"  [{r['status']}] depth={r['depth']}  {r['title'][:30]}  {r['url']}")
        out = os.path.join(os.path.dirname(__file__), "crawl_result.json")
        crawler.save_results(out)
        print(f"  结果保存到: {out}")
        # 清理
        if os.path.exists(out):
            os.remove(out)
    except Exception as e:
        print(f"  网络爬取失败（离线环境正常）: {e}")

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
