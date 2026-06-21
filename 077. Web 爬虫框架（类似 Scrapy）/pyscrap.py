# -*- coding: utf-8 -*-
"""
PyScrap —— 一个类 Scrapy 的迷你 Web 爬虫框架（纯标准库）

设计目标：用最少的代码实现 Scrapy 的核心抽象：
    Spider     用户写的爬虫，定义 start_urls 与 parse()
    Request    对一次 HTTP 请求的描述（url, method, headers, callback, meta...）
    Response   对响应的封装，提供 .css 替代品（极简 selector）/ .text / .url
    Item       使用 dict 即可
    Pipeline   处理 item（去重、保存到 jsonl 等）
    Scheduler  请求队列（FIFO + 已访问集合）
    Downloader 通过 urllib 下载，可选并发（线程池）
    Engine     调度 + 下载 + 解析的主循环

中间件：DownloaderMiddleware，process_request / process_response 钩子。

示例：QuotesSpider 抓取本地内置 HTML（不联网也能跑）
用法：
    python pyscrap.py                  # 跑示例 spider
    python pyscrap.py http://...       # 用通用 spider 抓一个 URL
"""
import os
import sys
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import html.parser
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Callable, Optional, Iterable, List, Dict, Any


# ============================================================
# Request / Response
# ============================================================
@dataclass
class Request:
    url: str
    callback: Optional[Callable] = None
    method: str = "GET"
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[bytes] = None
    meta: Dict[str, Any] = field(default_factory=dict)
    dont_filter: bool = False

    def __hash__(self):
        return hash((self.method, self.url))


class _SimpleSelectorParser(html.parser.HTMLParser):
    """收集所有标签 + 属性 + 文本，支持极简的 css(".cls"/"#id"/"tag") 查询。"""
    def __init__(self):
        super().__init__()
        # nodes: list of dict(tag, attrs, text, start, end)
        self.nodes = []
        self.stack = []

    def handle_starttag(self, tag, attrs):
        node = {"tag": tag, "attrs": dict(attrs), "text": "", "children": []}
        if self.stack:
            self.stack[-1]["children"].append(node)
        else:
            self.nodes.append(node)
        self.stack.append(node)

    def handle_endtag(self, tag):
        # 兼容嵌套异常
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]["tag"] == tag:
                self.stack = self.stack[:i]
                break

    def handle_startendtag(self, tag, attrs):
        node = {"tag": tag, "attrs": dict(attrs), "text": "", "children": []}
        if self.stack:
            self.stack[-1]["children"].append(node)
        else:
            self.nodes.append(node)

    def handle_data(self, data):
        if self.stack:
            self.stack[-1]["text"] += data


def _walk(nodes):
    for n in nodes:
        yield n
        yield from _walk(n["children"])


class Selector:
    """极简 CSS-like：tag / .class / #id；不支持组合选择器。"""
    def __init__(self, nodes):
        self.nodes = nodes

    def css(self, sel: str) -> "Selector":
        sel = sel.strip()
        result = []
        for n in _walk(self.nodes):
            if sel.startswith("#"):
                if n["attrs"].get("id") == sel[1:]:
                    result.append(n)
            elif sel.startswith("."):
                cls = n["attrs"].get("class", "")
                if sel[1:] in cls.split():
                    result.append(n)
            else:
                if n["tag"] == sel.lower():
                    result.append(n)
        return Selector(result)

    def get(self, attr: Optional[str] = None) -> Optional[str]:
        if not self.nodes:
            return None
        n = self.nodes[0]
        if attr is None:
            return n["text"].strip() or _all_text(n).strip()
        return n["attrs"].get(attr)

    def getall(self, attr: Optional[str] = None) -> List[str]:
        out = []
        for n in self.nodes:
            if attr is None:
                out.append((n["text"].strip() or _all_text(n)).strip())
            else:
                v = n["attrs"].get(attr)
                if v is not None:
                    out.append(v)
        return out

    def __iter__(self):
        for n in self.nodes:
            yield Selector([n])

    def __len__(self):
        return len(self.nodes)


def _all_text(node):
    s = node["text"]
    for c in node["children"]:
        s += _all_text(c)
    return s


@dataclass
class Response:
    url: str
    status: int
    headers: Dict[str, str]
    body: bytes
    request: Request

    @property
    def text(self) -> str:
        enc = "utf-8"
        ct = self.headers.get("Content-Type", "")
        if "charset=" in ct:
            enc = ct.split("charset=", 1)[1].split(";")[0].strip()
        try:
            return self.body.decode(enc, errors="replace")
        except LookupError:
            return self.body.decode("utf-8", errors="replace")

    @property
    def selector(self) -> Selector:
        if not hasattr(self, "_sel"):
            p = _SimpleSelectorParser()
            try:
                p.feed(self.text)
            except Exception:
                pass
            self._sel = Selector(p.nodes)
        return self._sel

    def css(self, sel: str) -> Selector:
        return self.selector.css(sel)

    def urljoin(self, href: str) -> str:
        return urllib.parse.urljoin(self.url, href)

    def follow(self, href: str, callback=None, **kw) -> Request:
        return Request(self.urljoin(href), callback=callback, **kw)


# ============================================================
# Spider
# ============================================================
class Spider:
    name = "spider"
    start_urls: List[str] = []
    custom_settings: Dict[str, Any] = {}

    def start_requests(self) -> Iterable[Request]:
        for u in self.start_urls:
            yield Request(u, callback=self.parse)

    def parse(self, response: Response):
        raise NotImplementedError


# ============================================================
# Scheduler
# ============================================================
class Scheduler:
    def __init__(self):
        self.queue = deque()
        self.seen = set()

    def push(self, req: Request):
        if not req.dont_filter:
            key = (req.method, req.url)
            if key in self.seen:
                return False
            self.seen.add(key)
        self.queue.append(req)
        return True

    def pop(self) -> Optional[Request]:
        if self.queue:
            return self.queue.popleft()
        return None

    def __len__(self):
        return len(self.queue)


# ============================================================
# Downloader (+ Middleware)
# ============================================================
class DownloaderMiddleware:
    def process_request(self, request: Request) -> Optional[Request]:
        return None  # 返回 None 则继续

    def process_response(self, request: Request, response: Response) -> Response:
        return response


class DefaultHeadersMiddleware(DownloaderMiddleware):
    def __init__(self, headers):
        self.headers = headers

    def process_request(self, request):
        for k, v in self.headers.items():
            request.headers.setdefault(k, v)


class Downloader:
    def __init__(self, timeout=10, middlewares=None):
        self.timeout = timeout
        self.middlewares = middlewares or []

    def fetch(self, request: Request) -> Optional[Response]:
        for mw in self.middlewares:
            mw.process_request(request)
        req = urllib.request.Request(
            request.url,
            data=request.body,
            method=request.method,
            headers=request.headers,
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read()
                resp_headers = {k: v for k, v in resp.headers.items()}
                response = Response(
                    url=resp.url,
                    status=resp.status,
                    headers=resp_headers,
                    body=body,
                    request=request,
                )
        except urllib.error.HTTPError as e:
            response = Response(
                url=request.url, status=e.code,
                headers=dict(e.headers or {}),
                body=e.read() if hasattr(e, "read") else b"",
                request=request,
            )
        except Exception as e:
            print(f"[downloader] {request.url} -> {e}")
            return None
        for mw in self.middlewares:
            response = mw.process_response(request, response)
        return response


# ============================================================
# Pipelines
# ============================================================
class Pipeline:
    def open(self): pass
    def process_item(self, item, spider): return item
    def close(self): pass


class JsonLinesPipeline(Pipeline):
    def __init__(self, path):
        self.path = path
        self.fh = None

    def open(self):
        self.fh = open(self.path, "w", encoding="utf-8")

    def process_item(self, item, spider):
        self.fh.write(json.dumps(item, ensure_ascii=False) + "\n")
        return item

    def close(self):
        if self.fh:
            self.fh.close()


class DedupPipeline(Pipeline):
    def __init__(self, key="id"):
        self.key = key
        self.seen = set()

    def process_item(self, item, spider):
        if self.key in item:
            v = item[self.key]
            if v in self.seen:
                return None
            self.seen.add(v)
        return item


class PrintPipeline(Pipeline):
    def process_item(self, item, spider):
        print(f"  >> ITEM: {item}")
        return item


# ============================================================
# Engine
# ============================================================
class Engine:
    def __init__(self, spider: Spider, pipelines=None, middlewares=None,
                 concurrency=4, delay=0.0):
        self.spider = spider
        self.scheduler = Scheduler()
        self.downloader = Downloader(middlewares=middlewares or [
            DefaultHeadersMiddleware({"User-Agent": "PyScrap/0.1 (+demo)"})
        ])
        self.pipelines = pipelines or []
        self.concurrency = max(1, concurrency)
        self.delay = delay
        self.stats = {"requests": 0, "responses": 0, "items": 0, "errors": 0}

    def crawl(self):
        for p in self.pipelines:
            p.open()

        for r in self.spider.start_requests():
            self.scheduler.push(r)

        try:
            with ThreadPoolExecutor(max_workers=self.concurrency) as pool:
                while len(self.scheduler):
                    # 取一批一起下
                    batch = []
                    while len(batch) < self.concurrency and len(self.scheduler):
                        req = self.scheduler.pop()
                        if req:
                            batch.append(req)
                    if not batch:
                        break
                    self.stats["requests"] += len(batch)
                    futs = [pool.submit(self.downloader.fetch, r) for r in batch]
                    for r, f in zip(batch, futs):
                        resp = f.result()
                        if resp is None:
                            self.stats["errors"] += 1
                            continue
                        self.stats["responses"] += 1
                        cb = r.callback or self.spider.parse
                        try:
                            output = cb(resp)
                        except Exception as e:
                            self.stats["errors"] += 1
                            print(f"[parse-err] {r.url}: {e}")
                            continue
                        if output is None:
                            continue
                        for x in output:
                            if isinstance(x, Request):
                                self.scheduler.push(x)
                            elif isinstance(x, dict):
                                self._dispatch_item(x)
                    if self.delay:
                        time.sleep(self.delay)
        finally:
            for p in self.pipelines:
                p.close()

        print("\n[engine] stats:", self.stats)

    def _dispatch_item(self, item):
        self.stats["items"] += 1
        for p in self.pipelines:
            item = p.process_item(item, self.spider)
            if item is None:
                return


# ============================================================
# 内置示例：QuotesSpider（用本地 HTML 字符串，不联网）
# ============================================================
LOCAL_HTML = {
    "local://list": """
        <html><body>
          <h1>Quotes</h1>
          <div class="quote">
            <span class="text">The world as we have created it is a process of our thinking.</span>
            <span class="author">Albert Einstein</span>
            <a class="next" href="local://page2">next</a>
          </div>
          <div class="quote">
            <span class="text">It is our choices that show what we truly are.</span>
            <span class="author">J.K. Rowling</span>
          </div>
        </body></html>
    """,
    "local://page2": """
        <html><body>
          <div class="quote">
            <span class="text">There is nothing permanent except change.</span>
            <span class="author">Heraclitus</span>
          </div>
        </body></html>
    """,
}


class _LocalDownloader(Downloader):
    """演示 Spider 时用，把 local:// 当作内置 HTML 源。"""
    def fetch(self, request: Request):
        if request.url in LOCAL_HTML:
            body = LOCAL_HTML[request.url].encode("utf-8")
            return Response(
                url=request.url,
                status=200,
                headers={"Content-Type": "text/html; charset=utf-8"},
                body=body, request=request,
            )
        return super().fetch(request)


class QuotesSpider(Spider):
    name = "quotes"
    start_urls = ["local://list"]

    def parse(self, response: Response):
        for q in response.css(".quote"):
            yield {
                "text": q.css(".text").get(),
                "author": q.css(".author").get(),
            }
        nxt = response.css(".next").get("href")
        if nxt:
            yield response.follow(nxt, callback=self.parse)


# ============================================================
# 通用 Spider —— 仅抓首页并打印 <a> 链接
# ============================================================
class LinksSpider(Spider):
    name = "links"

    def __init__(self, url):
        self.start_urls = [url]

    def parse(self, response: Response):
        print(f"[parse] {response.url} status={response.status} bytes={len(response.body)}")
        for a in response.css("a"):
            href = a.get("href")
            text = (a.get() or "").strip()[:40]
            if href:
                yield {"url": response.urljoin(href), "text": text}


# ============================================================
# CLI
# ============================================================
def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "items.jsonl")

    if len(sys.argv) >= 2 and sys.argv[1].startswith(("http://", "https://")):
        spider = LinksSpider(sys.argv[1])
        engine = Engine(spider,
                        pipelines=[PrintPipeline(), JsonLinesPipeline(out)],
                        concurrency=4, delay=0.3)
        engine.crawl()
        print(f"-> {out}")
        return

    # 默认跑内置 demo
    print("[demo] running QuotesSpider against local HTML...\n")
    spider = QuotesSpider()
    engine = Engine(spider,
                    pipelines=[DedupPipeline(key="text"),
                               PrintPipeline(),
                               JsonLinesPipeline(out)],
                    concurrency=2)
    # 替换 downloader 以支持 local:// 源
    engine.downloader = _LocalDownloader(middlewares=engine.downloader.middlewares)
    engine.crawl()
    print(f"\n-> items written to {out}")


if __name__ == "__main__":
    main()
