"""
纯 Python 搜索引擎 - 爬虫模块
支持 BFS 爬取、HTML 解析、链接提取、文本提取
"""

import re
import time
import hashlib
from urllib.parse import urljoin, urlparse
from html.parser import HTMLParser
from collections import deque

try:
    import requests
except ImportError:
    requests = None


# ───────────────────── HTML 文本提取器（纯 Python） ─────────────────────

class HTMLTextExtractor(HTMLParser):
    """从 HTML 中提取纯文本和链接，不依赖 BeautifulSoup"""

    IGNORE_TAGS = {"script", "style", "noscript", "head", "meta", "link"}

    def __init__(self):
        super().__init__()
        self._text_parts: list[str] = []
        self._links: list[str] = []
        self._skip_depth = 0
        self._current_tag: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        tag = tag.lower()
        self._current_tag = tag
        if tag in self.IGNORE_TAGS:
            self._skip_depth += 1
        if tag == "a":
            for name, value in attrs:
                if name == "href" and value:
                    self._links.append(value)
        # 换行标签，插入空格分隔
        if tag in {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr"}:
            self._text_parts.append(" ")

    def handle_endtag(self, tag: str):
        tag = tag.lower()
        if tag in self.IGNORE_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)

    def handle_data(self, data: str):
        if self._skip_depth == 0:
            self._text_parts.append(data)

    def get_text(self) -> str:
        text = " ".join(self._text_parts)
        # 多空白合并
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def get_links(self) -> list[str]:
        return self._links


def extract_text_and_links(html: str) -> tuple[str, list[str]]:
    """从 HTML 中提取文本和链接"""
    parser = HTMLTextExtractor()
    try:
        parser.feed(html)
    except Exception:
        pass
    return parser.get_text(), parser.get_links()


# ───────────────────── 爬虫主体 ─────────────────────

class WebCrawler:
    """
    BFS 网络爬虫

    Parameters
    ----------
    max_pages : int
        最多爬取页面数
    max_depth : int
        最大爬取深度
    delay : float
        请求间隔秒数（礼貌爬取）
    timeout : int
        单次请求超时秒数
    allowed_domains : list[str] | None
        限制爬取域名，None 不限制
    """

    def __init__(
        self,
        max_pages: int = 100,
        max_depth: int = 3,
        delay: float = 0.5,
        timeout: int = 10,
        allowed_domains: list[str] | None = None,
    ):
        if requests is None:
            raise ImportError(
                "需要 requests 库，请运行: pip install requests"
            )
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.delay = delay
        self.timeout = timeout
        self.allowed_domains = allowed_domains

        # 存储爬取结果: doc_id -> {url, title, text, links}
        self.documents: dict[str, dict] = {}
        self._visited: set[str] = set()

    @staticmethod
    def _normalize_url(url: str) -> str:
        """标准化 URL（去除片段、末尾斜杠）"""
        parsed = urlparse(url)
        # 去除 fragment
        path = parsed.path.rstrip("/")
        return f"{parsed.scheme}://{parsed.netloc}{path}"

    @staticmethod
    def _make_doc_id(url: str) -> str:
        """根据 URL 生成文档 ID"""
        return hashlib.md5(url.encode()).hexdigest()[:12]

    def _is_allowed(self, url: str) -> bool:
        """检查 URL 是否在允许范围内"""
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        if self.allowed_domains:
            return parsed.netloc in self.allowed_domains
        return True

    def _fetch(self, url: str) -> tuple[str, int] | None:
        """获取网页内容，返回 (html, status_code) 或 None"""
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (compatible; PySearchEngine/1.0; "
                    "+https://github.com/example)"
                )
            }
            resp = requests.get(url, headers=headers, timeout=self.timeout)
            content_type = resp.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                return None
            resp.encoding = resp.apparent_encoding or "utf-8"
            return resp.text, resp.status_code
        except Exception as e:
            print(f"  [!] 获取失败 {url}: {e}")
            return None

    @staticmethod
    def _extract_title(html: str) -> str:
        """简单提取 <title> 内容"""
        m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        if m:
            return re.sub(r"\s+", " ", m.group(1)).strip()
        return ""

    def crawl(self, seed_urls: list[str]) -> dict[str, dict]:
        """
        从种子 URL 开始 BFS 爬取

        Parameters
        ----------
        seed_urls : list[str]
            种子 URL 列表

        Returns
        -------
        dict[str, dict]
            文档集合 {doc_id: {url, title, text}}
        """
        queue: deque[tuple[str, int]] = deque()
        for url in seed_urls:
            norm = self._normalize_url(url)
            if norm not in self._visited:
                queue.append((norm, 0))
                self._visited.add(norm)

        count = 0
        while queue and count < self.max_pages:
            url, depth = queue.popleft()
            if depth > self.max_depth:
                continue
            if not self._is_allowed(url):
                continue

            print(f"  [{count + 1}/{self.max_pages}] 爬取 (深度 {depth}): {url}")
            result = self._fetch(url)
            if result is None:
                continue

            html, status = result
            text, links = extract_text_and_links(html)
            title = self._extract_title(html)

            if not text.strip():
                continue

            doc_id = self._make_doc_id(url)
            self.documents[doc_id] = {
                "url": url,
                "title": title or url,
                "text": text,
            }
            count += 1

            # 将新链接加入队列
            if depth < self.max_depth:
                for link in links:
                    abs_url = urljoin(url, link)
                    norm_url = self._normalize_url(abs_url)
                    if norm_url not in self._visited and self._is_allowed(norm_url):
                        self._visited.add(norm_url)
                        queue.append((norm_url, depth + 1))

            # 礼貌延迟
            time.sleep(self.delay)

        print(f"\n  爬取完成: 共 {len(self.documents)} 个页面")
        return self.documents


# ───────────────────── 演示入口 ─────────────────────

if __name__ == "__main__":
    crawler = WebCrawler(
        max_pages=10,
        max_depth=2,
        delay=0.5,
        allowed_domains=["example.com"],
    )
    docs = crawler.crawl(["https://example.com"])
    for doc_id, doc in docs.items():
        print(f"\n--- {doc_id} ---")
        print(f"  标题: {doc['title']}")
        print(f"  URL:  {doc['url']}")
        print(f"  文本 (前200字): {doc['text'][:200]}")
