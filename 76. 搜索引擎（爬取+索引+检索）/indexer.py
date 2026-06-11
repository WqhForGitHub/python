"""
纯 Python 搜索引擎 - 倒排索引模块
支持分词、倒排索引构建、TF-IDF 计算、索引持久化
"""

import json
import math
import re
import os
from collections import defaultdict


# ───────────────────── 英文分词器 ─────────────────────

# 简单的英文停用词
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "am", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can", "not",
    "no", "nor", "so", "if", "then", "than", "too", "very", "just",
    "about", "above", "after", "again", "all", "also", "any", "as",
    "because", "before", "between", "both", "each", "few", "here",
    "how", "into", "more", "most", "other", "out", "over", "own",
    "same", "some", "such", "that", "there", "these", "this", "those",
    "through", "under", "until", "up", "when", "where", "which", "while",
    "who", "whom", "why", "what", "it", "its", "he", "she", "they",
    "them", "we", "you", "i", "me", "my", "your", "his", "her",
    "our", "their", "this", "these", "those",
    # 中文常见停用词
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都",
    "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会",
    "着", "没有", "看", "好", "自己", "这",
}


def tokenize(text: str) -> list[str]:
    """
    分词：支持中英文混合文本

    - 英文：转小写 + 正则提取单词
    - 中文：按单字符切分（简易方案，无需 jieba）
    """
    tokens: list[str] = []
    # 提取英文单词
    for word in re.findall(r"[a-zA-Z]+", text):
        word = word.lower()
        if word not in STOP_WORDS and len(word) > 1:
            tokens.append(word)
    # 提取中文字符
    for ch in re.findall(r"[\u4e00-\u9fff]", text):
        if ch not in STOP_WORDS:
            tokens.append(ch)
    return tokens


# ───────────────────── 倒排索引 ─────────────────────

class InvertedIndex:
    """
    倒排索引 + TF-IDF

    数据结构
    --------
    index : dict[str, dict[str, list[int]]]
        term -> {doc_id: [positions]}

    doc_lengths : dict[str, int]
        doc_id -> 文档词数

    doc_count : int
        文档总数
    """

    def __init__(self):
        self.index: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
        self.doc_lengths: dict[str, int] = {}
        self.doc_count: int = 0
        # 保存文档元信息（标题、URL）
        self.doc_meta: dict[str, dict] = {}

    def add_document(self, doc_id: str, text: str, meta: dict | None = None):
        """
        将一个文档加入索引

        Parameters
        ----------
        doc_id : str
            文档唯一标识
        text : str
            文档正文
        meta : dict | None
            文档元信息（如 title, url）
        """
        tokens = tokenize(text)
        self.doc_lengths[doc_id] = len(tokens)
        self.doc_count += 1

        if meta:
            self.doc_meta[doc_id] = meta

        for pos, token in enumerate(tokens):
            self.index[token][doc_id].append(pos)

    def build_from_documents(self, documents: dict[str, dict]):
        """
        批量构建索引

        Parameters
        ----------
        documents : dict[str, dict]
            {doc_id: {text, title, url, ...}}
        """
        for doc_id, doc in documents.items():
            meta = {k: v for k, v in doc.items() if k != "text"}
            self.add_document(doc_id, doc["text"], meta)
        print(f"  索引构建完成: {self.doc_count} 篇文档, {len(self.index)} 个词项")

    # ───────────── TF-IDF 计算 ─────────────

    def tf(self, term: str, doc_id: str) -> float:
        """词频 (TF): 词在文档中出现的次数 / 文档总词数"""
        if doc_id not in self.index.get(term, {}):
            return 0.0
        count = len(self.index[term][doc_id])
        length = self.doc_lengths.get(doc_id, 1)
        return count / length

    def idf(self, term: str) -> float:
        """逆文档频率 (IDF): log(N / df)"""
        df = len(self.index.get(term, {}))
        if df == 0:
            return 0.0
        return math.log(self.doc_count / df)

    def tfidf(self, term: str, doc_id: str) -> float:
        """TF-IDF = TF * IDF"""
        return self.tf(term, doc_id) * self.idf(term)

    def doc_tfidf_vector(self, doc_id: str) -> dict[str, float]:
        """获取文档的 TF-IDF 向量（稀疏表示）"""
        vector: dict[str, float] = {}
        for term, postings in self.index.items():
            if doc_id in postings:
                vector[term] = self.tfidf(term, doc_id)
        return vector

    # ───────────── 索引持久化 ─────────────

    def save(self, filepath: str):
        """将索引保存到 JSON 文件"""
        data = {
            "index": {term: dict(postings) for term, postings in self.index.items()},
            "doc_lengths": self.doc_lengths,
            "doc_count": self.doc_count,
            "doc_meta": self.doc_meta,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  索引已保存: {filepath}")

    @classmethod
    def load(cls, filepath: str) -> "InvertedIndex":
        """从 JSON 文件加载索引"""
        idx = cls()
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        # 重建 index（需要转回 defaultdict）
        for term, postings in data["index"].items():
            for doc_id, positions in postings.items():
                idx.index[term][doc_id] = positions
        idx.doc_lengths = data["doc_lengths"]
        idx.doc_count = data["doc_count"]
        idx.doc_meta = data.get("doc_meta", {})
        print(f"  索引已加载: {filepath} ({idx.doc_count} 篇文档, {len(idx.index)} 个词项)")
        return idx

    def stats(self) -> dict:
        """返回索引统计信息"""
        total_terms = sum(self.doc_lengths.values())
        avg_dl = total_terms / self.doc_count if self.doc_count else 0
        return {
            "文档数": self.doc_count,
            "词项数": len(self.index),
            "总词数": total_terms,
            "平均文档长度": round(avg_dl, 1),
        }


# ───────────────────── 演示入口 ─────────────────────

if __name__ == "__main__":
    # 用内置示例数据演示
    sample_docs = {
        "doc1": {
            "url": "https://example.com/python",
            "title": "Python 教程",
            "text": "Python is a popular programming language. Python is easy to learn and powerful.",
        },
        "doc2": {
            "url": "https://example.com/java",
            "title": "Java 教程",
            "text": "Java is a widely used programming language. Java runs on many platforms.",
        },
        "doc3": {
            "url": "https://example.com/search",
            "title": "搜索引擎原理",
            "text": "Search engines use inverted index to find documents quickly. TF-IDF is a ranking method.",
        },
    }

    idx = InvertedIndex()
    idx.build_from_documents(sample_docs)

    print("\n索引统计:", idx.stats())

    # 演示 TF-IDF
    for term in ["python", "java", "search"]:
        print(f"\n词项: '{term}'")
        print(f"  IDF = {idx.idf(term):.4f}")
        for doc_id in sample_docs:
            score = idx.tfidf(term, doc_id)
            if score > 0:
                print(f"  TF-IDF({doc_id}) = {score:.4f}")
