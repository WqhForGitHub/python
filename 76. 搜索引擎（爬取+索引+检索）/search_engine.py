# -*- coding: utf-8 -*-
"""
搜索引擎（爬取 + 索引 + 检索）
- 纯 Python 实现，仅用标准库
- 三大模块：
    Crawler  : 基于 urllib 的简易广度优先爬虫（同域名限制）
    Indexer  : 倒排索引 + TF-IDF 权重 + 文档存储（pickle 持久化）
    Searcher : 支持多词查询、TF-IDF 排名、片段高亮

用法：
    python search_engine.py crawl <起始URL> [--max=20] [--same-host]
    python search_engine.py index
    python search_engine.py search "关键词 1 关键词 2"
    python search_engine.py demo            # 用本地内置文档跑一遍

数据目录：./se_data/
    pages/   抓取的页面（每篇一个文件）
    index.pkl 倒排索引
    docs.pkl  文档元信息
"""
import os
import sys
import math
import pickle
import urllib.request
import urllib.parse
import urllib.error
import html.parser
import re
from collections import defaultdict, Counter

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "se_data")
PAGES_DIR = os.path.join(DATA_DIR, "pages")
INDEX_PATH = os.path.join(DATA_DIR, "index.pkl")
DOCS_PATH = os.path.join(DATA_DIR, "docs.pkl")


# =============== HTML 解析 ===============
class HTMLTextExtractor(html.parser.HTMLParser):
    """提取纯文本 + 链接 + 标题。"""
    SKIP_TAGS = {"script", "style", "noscript"}

    def __init__(self):
        super().__init__()
        self.parts = []
        self.links = []
        self.title = ""
        self._in_skip = 0
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self._in_skip += 1
        if tag == "title":
            self._in_title = True
        if tag == "a":
            for k, v in attrs:
                if k.lower() == "href" and v:
                    self.links.append(v)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in self.SKIP_TAGS and self._in_skip > 0:
            self._in_skip -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_skip:
            return
        if self._in_title:
            self.title += data
        self.parts.append(data)

    def text(self):
        return " ".join(p.strip() for p in self.parts if p.strip())


def parse_html(raw_html):
    p = HTMLTextExtractor()
    try:
        p.feed(raw_html)
    except Exception:
        pass
    return p.title.strip(), p.text(), p.links


# =============== 分词 / 文本规范化 ===============
# 这个分词器很简单：按非字母/数字/中文切，并对中文做单字切分
_CJK_RANGE = (
    (0x4E00, 0x9FFF),
    (0x3400, 0x4DBF),
    (0xF900, 0xFAFF),
)


def _is_cjk(ch):
    cp = ord(ch)
    for lo, hi in _CJK_RANGE:
        if lo <= cp <= hi:
            return True
    return False


def tokenize(text):
    text = text.lower()
    tokens = []
    buf = []
    for ch in text:
        if _is_cjk(ch):
            if buf:
                tokens.append("".join(buf))
                buf = []
            tokens.append(ch)
        elif ch.isalnum():
            buf.append(ch)
        else:
            if buf:
                tokens.append("".join(buf))
                buf = []
    if buf:
        tokens.append("".join(buf))
    # 简单停用词
    stop = {"the", "a", "an", "of", "in", "on", "to", "is", "and", "or",
            "for", "with", "by", "be", "this", "that", "it", "as", "at",
            "from", "are", "was", "were", "but", "not", "no",
            "的", "了", "和", "是", "在", "也"}
    return [t for t in tokens if t and t not in stop]


# =============== 爬虫 ===============
class Crawler:
    USER_AGENT = "PySE/0.1 (+demo)"

    def __init__(self, max_pages=20, same_host_only=True, timeout=8):
        self.max_pages = max_pages
        self.same_host_only = same_host_only
        self.timeout = timeout
        os.makedirs(PAGES_DIR, exist_ok=True)

    def fetch(self, url):
        req = urllib.request.Request(url, headers={"User-Agent": self.USER_AGENT})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            ctype = resp.headers.get("Content-Type", "")
            if "html" not in ctype and "text" not in ctype:
                return None
            charset = "utf-8"
            m = re.search(r"charset=([\w\-]+)", ctype, re.I)
            if m:
                charset = m.group(1)
            data = resp.read()
            try:
                return data.decode(charset, errors="replace")
            except LookupError:
                return data.decode("utf-8", errors="replace")

    def crawl(self, seed_url):
        seed_url = seed_url.strip()
        seen = set()
        queue = [seed_url]
        seed_host = urllib.parse.urlparse(seed_url).netloc
        saved = []

        while queue and len(saved) < self.max_pages:
            url = queue.pop(0)
            if url in seen:
                continue
            seen.add(url)
            try:
                raw = self.fetch(url)
            except (urllib.error.URLError, urllib.error.HTTPError, ConnectionError, TimeoutError) as e:
                print(f"[skip] {url}: {e}")
                continue
            except Exception as e:
                print(f"[err]  {url}: {e}")
                continue
            if not raw:
                continue

            title, text, links = parse_html(raw)
            page_id = self._save_page(url, title, text)
            saved.append((page_id, url, title))
            print(f"[ok]   #{page_id} {url}  ({len(text)} chars)")

            for href in links:
                full = urllib.parse.urljoin(url, href).split("#", 1)[0]
                if not full.startswith(("http://", "https://")):
                    continue
                if self.same_host_only and urllib.parse.urlparse(full).netloc != seed_host:
                    continue
                if full not in seen:
                    queue.append(full)

        print(f"\nCrawl finished. Saved {len(saved)} pages -> {PAGES_DIR}")
        return saved

    def _save_page(self, url, title, text):
        # 用现有文件数作为 id（保证按抓取顺序递增）
        existing = [f for f in os.listdir(PAGES_DIR) if f.endswith(".pkl")]
        page_id = len(existing) + 1
        path = os.path.join(PAGES_DIR, f"{page_id:05d}.pkl")
        with open(path, "wb") as f:
            pickle.dump({"id": page_id, "url": url, "title": title, "text": text}, f)
        return page_id


# =============== 索引 ===============
class Indexer:
    """
    倒排索引：term -> { doc_id -> tf }
    文档表：doc_id -> {url, title, length, snippet}
    """
    def __init__(self):
        self.inverted = defaultdict(dict)
        self.docs = {}

    def add_doc(self, doc_id, url, title, text):
        toks = tokenize(text)
        if not toks:
            return
        tf = Counter(toks)
        for term, c in tf.items():
            self.inverted[term][doc_id] = c
        self.docs[doc_id] = {
            "url": url,
            "title": title or url,
            "length": len(toks),
            "snippet": text[:200],
        }

    def build_from_pages(self):
        if not os.path.isdir(PAGES_DIR):
            print("No pages dir.")
            return
        files = sorted(f for f in os.listdir(PAGES_DIR) if f.endswith(".pkl"))
        for fn in files:
            with open(os.path.join(PAGES_DIR, fn), "rb") as f:
                p = pickle.load(f)
            self.add_doc(p["id"], p["url"], p["title"], p["text"])
        self.save()
        print(f"Indexed {len(self.docs)} docs / {len(self.inverted)} terms.")

    def save(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(INDEX_PATH, "wb") as f:
            pickle.dump(dict(self.inverted), f)
        with open(DOCS_PATH, "wb") as f:
            pickle.dump(self.docs, f)

    def load(self):
        if not (os.path.exists(INDEX_PATH) and os.path.exists(DOCS_PATH)):
            return False
        with open(INDEX_PATH, "rb") as f:
            self.inverted = defaultdict(dict, pickle.load(f))
        with open(DOCS_PATH, "rb") as f:
            self.docs = pickle.load(f)
        return True


# =============== 检索 ===============
class Searcher:
    def __init__(self, indexer):
        self.idx = indexer
        self.N = max(1, len(indexer.docs))

    def search(self, query, topk=10):
        terms = tokenize(query)
        if not terms:
            return []
        # 计算 idf
        idf = {}
        for t in terms:
            df = len(self.idx.inverted.get(t, {}))
            idf[t] = math.log((self.N + 1) / (df + 1)) + 1.0
        # 累加每个候选文档的得分
        scores = defaultdict(float)
        for t in terms:
            postings = self.idx.inverted.get(t, {})
            for doc_id, tf in postings.items():
                doc_len = self.idx.docs[doc_id]["length"] or 1
                # 长度归一化的 tf-idf
                scores[doc_id] += (tf / doc_len) * idf[t]
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:topk]
        results = []
        for doc_id, sc in ranked:
            d = self.idx.docs[doc_id]
            results.append({
                "score": sc,
                "url": d["url"],
                "title": d["title"],
                "snippet": self._highlight(d["snippet"], terms),
            })
        return results

    @staticmethod
    def _highlight(text, terms):
        out = text
        for t in sorted(set(terms), key=len, reverse=True):
            # 简单替换（忽略大小写）
            i = 0
            lower = out.lower()
            tl = t.lower()
            chunks = []
            while True:
                p = lower.find(tl, i)
                if p < 0:
                    chunks.append(out[i:])
                    break
                chunks.append(out[i:p])
                chunks.append("[" + out[p:p+len(t)] + "]")
                i = p + len(t)
            out = "".join(chunks)
            lower = out.lower()
        return out


# =============== Demo 数据 ===============
DEMO_DOCS = [
    ("local://intro",   "Python 简介",
     "Python 是一种解释型、面向对象的通用编程语言，语法简洁优雅，被广泛用于 Web 开发、数据分析与人工智能。"),
    ("local://web",     "Python Web 开发",
     "使用 Python 进行 Web 开发可以选择 Flask、Django 等框架，本文介绍 Flask 入门以及路由、模板、表单的基本知识。"),
    ("local://crawl",   "Python 爬虫",
     "Python 爬虫常用 requests 与 BeautifulSoup，本文用纯标准库 urllib 与 html.parser 抓取页面，并讲解索引与搜索。"),
    ("local://index",   "倒排索引",
     "倒排索引是搜索引擎的核心数据结构。它将每个词映射到包含该词的文档列表，配合 TF-IDF 可以实现关键词排名。"),
    ("local://rank",    "TF-IDF 与排名",
     "TF-IDF 衡量一个词在文档中的重要性：词频越高越重要，但出现在很多文档中的词权重会被降低。它是搜索排序的基础。"),
    ("local://misc",    "其它",
     "本 Demo 演示纯 Python 实现的搜索引擎，包括爬虫、索引和检索三大部分，运行不依赖任何第三方库。"),
]


def run_demo():
    os.makedirs(DATA_DIR, exist_ok=True)
    idx = Indexer()
    for i, (url, title, text) in enumerate(DEMO_DOCS, start=1):
        idx.add_doc(i, url, title, text)
    idx.save()
    print(f"[demo] built index with {len(idx.docs)} docs.\n")

    s = Searcher(idx)
    for q in ["Python 爬虫", "TF-IDF 索引", "Web 框架", "搜索引擎"]:
        print(f"Query: {q}")
        for r in s.search(q, topk=3):
            print(f"  {r['score']:.4f}  {r['title']}  ({r['url']})")
            print(f"      {r['snippet']}")
        print()


# =============== CLI ===============
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]
    if cmd == "demo":
        run_demo()
        return

    if cmd == "crawl":
        if len(sys.argv) < 3:
            print("usage: crawl <url> [--max=N] [--same-host]")
            return
        url = sys.argv[2]
        max_pages = 20
        same_host = False
        for a in sys.argv[3:]:
            if a.startswith("--max="):
                max_pages = int(a.split("=", 1)[1])
            elif a == "--same-host":
                same_host = True
        Crawler(max_pages=max_pages, same_host_only=same_host).crawl(url)
        return

    if cmd == "index":
        Indexer().build_from_pages()
        return

    if cmd == "search":
        if len(sys.argv) < 3:
            print("usage: search \"keywords\"")
            return
        idx = Indexer()
        if not idx.load():
            print("No index found. Run `index` (or `demo`) first.")
            return
        q = " ".join(sys.argv[2:])
        s = Searcher(idx)
        results = s.search(q, topk=10)
        if not results:
            print("(no results)")
            return
        for r in results:
            print(f"{r['score']:.4f}  {r['title']}")
            print(f"        {r['url']}")
            print(f"        {r['snippet']}\n")
        return

    print("unknown command:", cmd)


if __name__ == "__main__":
    main()
