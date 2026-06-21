"""
简单搜索引擎（本地文件）
功能：
    - 扫描目录中的文本文件，构建倒排索引（term -> [(doc_id, tf)]）
    - 文档元信息：路径、长度、修改时间
    - 查询：
        * 单关键字
        * 多关键字（AND/OR）
        * 短语查询（基于位置索引）
        * TF-IDF 排序
        * 高亮返回
    - 支持中英文切词（中文按字切分 + 英文按 \w+ 切分）
    - 索引可序列化到 JSON 持久化
"""

import os
import re
import json
import math
from collections import defaultdict


TEXT_EXTS = {".txt", ".md", ".log", ".csv", ".json",
             ".py", ".js", ".html", ".css", ".rst"}


def tokenize(text: str) -> list:
    """简单切词：英文按 \\w+，中文按单字"""
    text = text.lower()
    tokens = []
    for m in re.finditer(r"[a-z0-9_]+|[\u4e00-\u9fff]", text):
        tokens.append(m.group(0))
    return tokens


class SearchEngine:
    """本地文件搜索引擎"""

    def __init__(self):
        self.docs = {}                # doc_id -> {path, length, mtime}
        self.inverted = defaultdict(dict)  # term -> {doc_id: [pos1, pos2 ...]}
        self.next_id = 0

    # -------- 索引构建 --------
    def add_file(self, path: str):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except OSError:
            return
        doc_id = self.next_id
        self.next_id += 1
        tokens = tokenize(text)
        for pos, tk in enumerate(tokens):
            self.inverted[tk].setdefault(doc_id, []).append(pos)
        self.docs[doc_id] = {
            "path": path,
            "length": len(tokens),
            "mtime": os.path.getmtime(path),
        }

    def index_dir(self, root: str, exts=TEXT_EXTS):
        for cur, dirs, files in os.walk(root):
            for fn in files:
                if os.path.splitext(fn)[1].lower() in exts:
                    self.add_file(os.path.join(cur, fn))

    # -------- 查询 --------
    def search(self, query: str, mode: str = "and", top: int = 10) -> list:
        """
        mode:
            'and'    所有词都要出现
            'or'     任一词出现
            'phrase' 必须连续短语
        """
        terms = tokenize(query)
        if not terms:
            return []

        if mode == "phrase":
            cand_docs = self._phrase_match(terms)
        elif mode == "and":
            sets = [set(self.inverted.get(t, {}).keys()) for t in terms]
            cand_docs = set.intersection(*sets) if sets else set()
        else:
            cand_docs = set()
            for t in terms:
                cand_docs |= set(self.inverted.get(t, {}).keys())

        # TF-IDF 排序
        results = []
        N = max(len(self.docs), 1)
        for did in cand_docs:
            score = 0.0
            for t in terms:
                postings = self.inverted.get(t, {})
                if did not in postings:
                    continue
                tf = len(postings[did]) / max(self.docs[did]["length"], 1)
                df = len(postings)
                idf = math.log((N + 1) / (df + 1)) + 1
                score += tf * idf
            results.append((did, score))

        results.sort(key=lambda x: -x[1])
        results = results[:top]

        out = []
        for did, score in results:
            doc = self.docs[did]
            snippet = self._snippet(doc["path"], terms)
            out.append({
                "path": doc["path"],
                "score": round(score, 4),
                "length": doc["length"],
                "snippet": snippet,
            })
        return out

    def _phrase_match(self, terms: list) -> set:
        """短语匹配：每个词必须依次出现且位置连续"""
        if not terms:
            return set()
        first = self.inverted.get(terms[0], {})
        result = set()
        for did, positions in first.items():
            for start in positions:
                ok = True
                for offset, t in enumerate(terms[1:], 1):
                    pos_list = self.inverted.get(t, {}).get(did, [])
                    if (start + offset) not in pos_list:
                        ok = False
                        break
                if ok:
                    result.add(did)
                    break
        return result

    def _snippet(self, path: str, terms: list, width: int = 30) -> str:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except OSError:
            return ""
        low = text.lower()
        for t in terms:
            i = low.find(t)
            if i >= 0:
                start = max(0, i - width)
                end = min(len(text), i + len(t) + width)
                snippet = text[start:end].replace("\n", " ")
                # 高亮（用 <<term>>）
                for tt in terms:
                    snippet = re.sub(
                        re.escape(tt), lambda m: f"<<{m.group(0)}>>",
                        snippet, flags=re.IGNORECASE,
                    )
                return ("..." if start > 0 else "") + snippet \
                       + ("..." if end < len(text) else "")
        return text[:60].replace("\n", " ")

    # -------- 持久化 --------
    def save(self, path: str):
        data = {
            "docs": self.docs,
            "next_id": self.next_id,
            "inverted": {
                t: {str(d): pos for d, pos in postings.items()}
                for t, postings in self.inverted.items()
            },
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def load(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.docs = {int(k): v for k, v in data["docs"].items()}
        self.next_id = data["next_id"]
        self.inverted = defaultdict(dict)
        for t, postings in data["inverted"].items():
            self.inverted[t] = {int(d): list(pos) for d, pos in postings.items()}

    def stats(self) -> dict:
        return {
            "docs": len(self.docs),
            "terms": len(self.inverted),
            "total_postings": sum(len(p) for p in self.inverted.values()),
        }


# ==================== Demo ====================

if __name__ == "__main__":
    import shutil

    print("=" * 60)
    print("  简单搜索引擎（本地文件） Demo")
    print("=" * 60)

    base = os.path.dirname(os.path.abspath(__file__))
    corpus = os.path.join(base, "corpus")
    if os.path.exists(corpus):
        shutil.rmtree(corpus)
    os.makedirs(corpus)

    docs = {
        "intro.md": "# Python 简介\nPython 是一门简洁优雅的编程语言。\n"
                    "它支持面向对象编程，也支持函数式编程。",
        "search.txt": "Search engine builds an inverted index "
                      "from document corpus. "
                      "TF-IDF is a classic ranking algorithm.",
        "tutorial.md": "学习 Python 入门教程：变量、循环、函数。\n"
                       "Python 是流行的编程语言，应用广泛。",
        "log.txt": "2025-10-01 INFO server started\n"
                   "2025-10-01 INFO request received from 127.0.0.1\n"
                   "2025-10-02 ERROR database connection failed",
        "english.txt": "The quick brown fox jumps over the lazy dog. "
                       "Hello world! Python rocks.",
    }
    for name, content in docs.items():
        with open(os.path.join(corpus, name), "w", encoding="utf-8") as f:
            f.write(content)

    # 1. 建索引
    print("\n--- 1. 建立索引 ---")
    se = SearchEngine()
    se.index_dir(corpus)
    s = se.stats()
    print(f"  文档数: {s['docs']},  词条数: {s['terms']},  "
          f"倒排项数: {s['total_postings']}")

    # 2. 单词查询
    print("\n--- 2. 查询 'python' ---")
    for r in se.search("python", top=5):
        print(f"  [{r['score']}] {os.path.basename(r['path'])}")
        print(f"    {r['snippet']}")

    # 3. 多关键字 AND
    print("\n--- 3. AND 查询 'python 编程' ---")
    for r in se.search("python 编程", mode="and"):
        print(f"  [{r['score']}] {os.path.basename(r['path'])}")
        print(f"    {r['snippet']}")

    # 4. OR
    print("\n--- 4. OR 查询 'fox database' ---")
    for r in se.search("fox database", mode="or"):
        print(f"  [{r['score']}] {os.path.basename(r['path'])}")
        print(f"    {r['snippet']}")

    # 5. 短语
    print("\n--- 5. 短语查询 'inverted index' ---")
    for r in se.search("inverted index", mode="phrase"):
        print(f"  [{r['score']}] {os.path.basename(r['path'])}")
        print(f"    {r['snippet']}")

    # 6. 中文短语
    print("\n--- 6. 中文短语 '编程语言' ---")
    for r in se.search("编程语言", mode="phrase"):
        print(f"  [{r['score']}] {os.path.basename(r['path'])}")
        print(f"    {r['snippet']}")

    # 7. 持久化
    print("\n--- 7. 索引持久化 ---")
    idx_file = os.path.join(base, "_index.json")
    se.save(idx_file)
    sz = os.path.getsize(idx_file)
    print(f"  保存到 {idx_file}, {sz} bytes")

    se2 = SearchEngine()
    se2.load(idx_file)
    print(f"  重新加载: {se2.stats()}")

    # 清理
    shutil.rmtree(corpus, ignore_errors=True)
    if os.path.exists(idx_file):
        os.remove(idx_file)

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
