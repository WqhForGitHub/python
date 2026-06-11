"""
纯 Python 搜索引擎 - 检索模块
支持 TF-IDF 余弦相似度、BM25 排序、关键词高亮
"""

import math
import re
from dataclasses import dataclass, field

from indexer import InvertedIndex, tokenize


# ───────────────────── 搜索结果 ─────────────────────

@dataclass
class SearchResult:
    """单条搜索结果"""
    doc_id: str
    score: float
    title: str = ""
    url: str = ""
    snippet: str = ""  # 摘要片段
    matched_terms: list[str] = field(default_factory=list)


# ───────────────────── 向量工具 ─────────────────────

def cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    """
    计算两个稀疏向量的余弦相似度
    vec = {term: weight}
    """
    # 只计算共同词项
    common = set(vec_a.keys()) & set(vec_b.keys())
    if not common:
        return 0.0

    dot = sum(vec_a[t] * vec_b[t] for t in common)
    norm_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
    norm_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))

    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ───────────────────── 搜索器 ─────────────────────

class Searcher:
    """
    搜索引擎检索器

    支持两种排序算法:
    1. TF-IDF 余弦相似度
    2. BM25
    """

    def __init__(self, index: InvertedIndex):
        self.index = index

    # ───────────── TF-IDF 余弦检索 ─────────────

    def search_tfidf(self, query: str, top_k: int = 10) -> list[SearchResult]:
        """
        使用 TF-IDF + 余弦相似度检索

        Parameters
        ----------
        query : str
            查询字符串
        top_k : int
            返回前 k 个结果

        Returns
        -------
        list[SearchResult]
            按相关度降序排列的搜索结果
        """
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        # 构建查询向量
        query_vec: dict[str, float] = {}
        for term in set(query_tokens):
            idf = self.index.idf(term)
            if idf > 0:
                # 查询中词频
                tf_q = query_tokens.count(term) / len(query_tokens)
                query_vec[term] = tf_q * idf

        if not query_vec:
            return []

        # 候选文档: 包含至少一个查询词项的文档
        candidate_docs: set[str] = set()
        for term in query_vec:
            candidate_docs.update(self.index.index.get(term, {}).keys())

        # 计算每个候选文档的余弦相似度
        results: list[SearchResult] = []
        for doc_id in candidate_docs:
            doc_vec = self.index.doc_tfidf_vector(doc_id)
            score = cosine_similarity(query_vec, doc_vec)
            if score > 0:
                meta = self.index.doc_meta.get(doc_id, {})
                matched = [t for t in query_vec if t in self.index.index and doc_id in self.index.index[t]]
                results.append(SearchResult(
                    doc_id=doc_id,
                    score=score,
                    title=meta.get("title", ""),
                    url=meta.get("url", ""),
                    matched_terms=matched,
                ))

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    # ───────────── BM25 检索 ─────────────

    def search_bm25(self, query: str, top_k: int = 10, k1: float = 1.5, b: float = 0.75) -> list[SearchResult]:
        """
        使用 BM25 算法检索

        BM25 公式:
        score(D, Q) = Σ IDF(qi) * (f(qi, D) * (k1 + 1)) / (f(qi, D) + k1 * (1 - b + b * |D| / avgdl))

        Parameters
        ----------
        query : str
            查询字符串
        top_k : int
            返回前 k 个结果
        k1 : float
            词频饱和参数
        b : float
            文档长度归一化参数
        """
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        # 计算平均文档长度
        total_length = sum(self.index.doc_lengths.values())
        avgdl = total_length / self.index.doc_count if self.index.doc_count else 1

        # 候选文档
        candidate_docs: set[str] = set()
        for term in set(query_tokens):
            candidate_docs.update(self.index.index.get(term, {}).keys())

        results: list[SearchResult] = []
        for doc_id in candidate_docs:
            score = 0.0
            matched: list[str] = []
            doc_len = self.index.doc_lengths.get(doc_id, 0)

            for term in set(query_tokens):
                postings = self.index.index.get(term, {})
                if doc_id not in postings:
                    continue

                # 词频
                freq = len(postings[doc_id])
                # IDF (BM25 变体，避免负值)
                df = len(postings)
                idf = math.log((self.index.doc_count - df + 0.5) / (df + 0.5) + 1)
                # BM25 评分
                numerator = freq * (k1 + 1)
                denominator = freq + k1 * (1 - b + b * doc_len / avgdl)
                score += idf * numerator / denominator
                matched.append(term)

            if score > 0:
                meta = self.index.doc_meta.get(doc_id, {})
                results.append(SearchResult(
                    doc_id=doc_id,
                    score=score,
                    title=meta.get("title", ""),
                    url=meta.get("url", ""),
                    matched_terms=matched,
                ))

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    # ───────────── 摘要 & 高亮 ─────────────

    @staticmethod
    def generate_snippet(text: str, query: str, max_length: int = 200) -> str:
        """
        生成搜索结果摘要，关键词高亮标记

        使用 **词项** 形式标记匹配词
        """
        query_tokens = set(tokenize(query))
        if not query_tokens:
            return text[:max_length]

        # 找到第一个匹配词的位置
        text_lower = text.lower()
        best_pos = 0
        for token in query_tokens:
            idx = text_lower.find(token)
            if idx != -1:
                best_pos = idx
                break

        # 截取片段
        start = max(0, best_pos - 40)
        snippet = text[start:start + max_length]
        if start > 0:
            snippet = "..." + snippet
        if start + max_length < len(text):
            snippet = snippet + "..."

        # 高亮关键词
        for token in query_tokens:
            pattern = re.compile(re.escape(token), re.IGNORECASE)
            snippet = pattern.sub(lambda m: f"**{m.group()}**", snippet)

        return snippet

    def search(
        self,
        query: str,
        top_k: int = 10,
        method: str = "bm25",
        with_snippet: bool = True,
    ) -> list[SearchResult]:
        """
        统一搜索接口

        Parameters
        ----------
        query : str
            查询字符串
        top_k : int
            返回前 k 个结果
        method : str
            排序方法: "bm25" 或 "tfidf"
        with_snippet : bool
            是否生成摘要
        """
        if method == "tfidf":
            results = self.search_tfidf(query, top_k)
        else:
            results = self.search_bm25(query, top_k)

        # 填充摘要
        if with_snippet:
            for r in results:
                doc_text = self.index.doc_meta.get(r.doc_id, {}).get("text", "")
                if not doc_text and r.doc_id in self.index.doc_lengths:
                    # 尝试从索引重建文本片段
                    doc_text = ""
                r.snippet = self.generate_snippet(doc_text, query)

        return results


# ───────────────────── 演示入口 ─────────────────────

if __name__ == "__main__":
    from indexer import InvertedIndex

    sample_docs = {
        "doc1": {
            "url": "https://example.com/python",
            "title": "Python 教程",
            "text": "Python is a popular programming language. Python is easy to learn and powerful. Many developers love Python.",
        },
        "doc2": {
            "url": "https://example.com/java",
            "title": "Java 教程",
            "text": "Java is a widely used programming language. Java runs on many platforms. Java is strongly typed.",
        },
        "doc3": {
            "url": "https://example.com/search",
            "title": "搜索引擎原理",
            "text": "Search engines use inverted index to find documents quickly. TF-IDF and BM25 are ranking methods.",
        },
    }

    idx = InvertedIndex()
    idx.build_from_documents(sample_docs)

    searcher = Searcher(idx)

    for query in ["python programming", "java language", "search engine", "programming"]:
        print(f"\n{'='*50}")
        print(f"查询: '{query}'")
        print(f"{'='*50}")

        print("\n--- BM25 ---")
        for r in searcher.search_bm25(query, top_k=3):
            print(f"  [{r.score:.4f}] {r.title} ({r.url})")
            print(f"         匹配词: {r.matched_terms}")

        print("\n--- TF-IDF ---")
        for r in searcher.search_tfidf(query, top_k=3):
            print(f"  [{r.score:.4f}] {r.title} ({r.url})")
            print(f"         匹配词: {r.matched_terms}")
