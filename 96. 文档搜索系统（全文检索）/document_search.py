"""
文档搜索系统（全文检索）- 纯 Python 实现
=====================================
功能：
- 文档加载（txt / 内嵌字符串）
- 倒排索引（term -> postings）
- TF-IDF 相关性评分
- 短语搜索 / 布尔查询（AND / OR / NOT）
- 高亮命中片段
- 结果分页

仅依赖标准库。
"""

import math
import os
import re
from collections import defaultdict, Counter


def tokenize(text):
    """分词 + 简单规范化（小写 + 去标点）"""
    text = text.lower()
    return re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", text)


# ---------- 倒排索引 ----------
class InvertedIndex:
    def __init__(self):
        # term -> {doc_id: [pos1, pos2, ...]}
        self.index = defaultdict(lambda: defaultdict(list))
        self.docs = {}        # doc_id -> raw text
        self.doc_meta = {}    # doc_id -> {title, length, ...}
        self.doc_count = 0

    def add_document(self, doc_id, text, title=None):
        self.docs[doc_id] = text
        tokens = tokenize(text)
        self.doc_meta[doc_id] = {
            "title": title or doc_id,
            "length": len(tokens),
        }
        for pos, term in enumerate(tokens):
            self.index[term][doc_id].append(pos)
        self.doc_count = len(self.docs)

    def add_directory(self, path):
        """从目录批量加载 .txt"""
        for fn in os.listdir(path):
            if fn.lower().endswith(".txt"):
                full = os.path.join(path, fn)
                with open(full, encoding="utf-8") as f:
                    self.add_document(fn, f.read(), title=fn)

    # ---------- TF-IDF ----------
    def idf(self, term):
        df = len(self.index.get(term, {}))
        if df == 0:
            return 0.0
        return math.log((self.doc_count + 1) / (df + 1)) + 1

    def tfidf_score(self, doc_id, terms):
        meta = self.doc_meta[doc_id]
        length = meta["length"] or 1
        score = 0.0
        for t in terms:
            postings = self.index.get(t, {})
            if doc_id in postings:
                tf = len(postings[doc_id]) / length
                score += tf * self.idf(t)
        return score

    # ---------- 查询 ----------
    def search(self, query, top_k=10):
        """支持 AND / OR / NOT，默认 OR"""
        terms_with_op = self._parse_query(query)
        candidate_docs = self._evaluate(terms_with_op)
        scored = []
        all_terms = [t for op, t in terms_with_op if t]
        for doc_id in candidate_docs:
            score = self.tfidf_score(doc_id, all_terms)
            scored.append((doc_id, score))
        scored.sort(key=lambda x: -x[1])
        return scored[:top_k]

    def phrase_search(self, phrase, top_k=10):
        """短语搜索：要求所有词在文档中连续出现"""
        terms = tokenize(phrase)
        if not terms:
            return []
        # 取出所有命中文档
        candidate = None
        for t in terms:
            docs = set(self.index.get(t, {}).keys())
            candidate = docs if candidate is None else candidate & docs
        results = []
        for doc_id in candidate or []:
            positions_lists = [self.index[t][doc_id] for t in terms]
            if self._has_consecutive(positions_lists):
                score = self.tfidf_score(doc_id, terms)
                results.append((doc_id, score))
        results.sort(key=lambda x: -x[1])
        return results[:top_k]

    @staticmethod
    def _has_consecutive(plists):
        """检查是否存在 p0, p0+1, p0+2... 都在对应列表中"""
        if not plists:
            return False
        first = plists[0]
        for p in first:
            ok = True
            for i, lst in enumerate(plists[1:], start=1):
                if (p + i) not in lst:
                    ok = False
                    break
            if ok:
                return True
        return False

    # ---------- 查询解析 ----------
    def _parse_query(self, query):
        """简单解析：词前可加 +(必须) -(排除)，否则当 OR"""
        out = []
        for tok in query.split():
            if tok.startswith("+"):
                out.append(("AND", tokenize(tok[1:])[0] if tokenize(tok[1:]) else None))
            elif tok.startswith("-"):
                out.append(("NOT", tokenize(tok[1:])[0] if tokenize(tok[1:]) else None))
            else:
                ts = tokenize(tok)
                for t in ts:
                    out.append(("OR", t))
        return [(op, t) for op, t in out if t]

    def _evaluate(self, terms_with_op):
        """根据 op 计算候选文档集合"""
        all_docs = set(self.docs.keys())
        must = []
        should = []
        must_not = []
        for op, t in terms_with_op:
            if op == "AND":
                must.append(t)
            elif op == "NOT":
                must_not.append(t)
            else:
                should.append(t)

        result = None
        if must:
            for t in must:
                docs = set(self.index.get(t, {}).keys())
                result = docs if result is None else result & docs
        if should and result is None:
            result = set()
            for t in should:
                result |= set(self.index.get(t, {}).keys())
        elif should and result is not None:
            # OR 词不影响过滤，但提供分数
            pass
        if result is None:
            result = all_docs
        for t in must_not:
            result -= set(self.index.get(t, {}).keys())
        return result

    # ---------- 高亮片段 ----------
    def snippet(self, doc_id, terms, window=30):
        text = self.docs[doc_id]
        lower = text.lower()
        # 找第一个匹配位置
        for t in terms:
            idx = lower.find(t)
            if idx != -1:
                start = max(0, idx - window)
                end = min(len(text), idx + len(t) + window)
                snip = text[start:end]
                # 用 [hit] 包裹
                for term in terms:
                    snip = re.sub(
                        f"({re.escape(term)})",
                        r"[\1]",
                        snip,
                        flags=re.IGNORECASE,
                    )
                return ("..." if start > 0 else "") + snip + ("..." if end < len(text) else "")
        return text[:60] + "..."


# ---------- Demo ----------
DEMO_DOCS = {
    "doc1.txt": "Python is a powerful programming language. It is widely used in data science and machine learning. Python supports multiple paradigms including object oriented and functional.",
    "doc2.txt": "Machine learning is a subset of artificial intelligence. Common algorithms include linear regression, decision trees, and neural networks. Python is a popular language for machine learning.",
    "doc3.txt": "Data science combines statistics, programming, and domain knowledge. Tools include Python, R, and SQL. Visualization is also an important part.",
    "doc4.txt": "Natural language processing helps computers understand human language. Tasks include sentiment analysis, translation, and chatbots.",
    "doc5.txt": "Deep learning uses neural networks with many layers. It powers modern speech recognition and image classification systems.",
}


def demo():
    idx = InvertedIndex()
    for k, v in DEMO_DOCS.items():
        idx.add_document(k, v, title=k)
    print(f"已索引 {idx.doc_count} 篇文档")
    print(f"词典大小: {len(idx.index)}\n")

    queries = [
        "python machine learning",
        "+python -language",
        "neural network",
    ]
    for q in queries:
        print(f"--- 查询: '{q}' ---")
        terms = [t for t in tokenize(q) if not t.startswith("-")]
        for doc_id, score in idx.search(q, top_k=3):
            snip = idx.snippet(doc_id, [t for op, t in idx._parse_query(q)])
            print(f"  [{score:.3f}] {doc_id}: {snip}")
        print()

    print("--- 短语搜索: 'machine learning' ---")
    for doc_id, score in idx.phrase_search("machine learning"):
        print(f"  [{score:.3f}] {doc_id}: {idx.snippet(doc_id, ['machine', 'learning'])}")


if __name__ == "__main__":
    demo()
