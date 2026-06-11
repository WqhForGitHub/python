#!/usr/bin/env python3
"""
纯 Python 搜索引擎 Demo
爬取 -> 索引 -> 检索 完整流程

用法:
  # 使用内置示例数据运行（无需网络）
  python main.py --demo

  # 爬取真实网页并搜索
  python main.py --crawl https://example.com --max-pages 20

  # 从已保存的索引文件加载并搜索
  python main.py --load index.json

  # 交互式搜索
  python main.py --demo --interactive
"""

import argparse
import json
import os
import sys

# 将当前目录加入 path，确保模块导入正常
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from indexer import InvertedIndex
from searcher import Searcher


# ───────────────────── 内置示例数据 ─────────────────────

SAMPLE_DOCS = {
    "doc1": {
        "url": "https://example.com/python",
        "title": "Python 编程语言入门",
        "text": (
            "Python 是一种广泛使用的高级编程语言。Python 的设计哲学强调代码的可读性和简洁性。"
            "Python 支持多种编程范式，包括面向对象、命令式、函数式和过程式编程。"
            "Python 拥有庞大的标准库和丰富的第三方包生态系统，被广泛应用于 Web 开发、数据科学、人工智能等领域。"
            "Python 的语法简单直观，非常适合初学者学习编程。"
        ),
    },
    "doc2": {
        "url": "https://example.com/java",
        "title": "Java 编程语言指南",
        "text": (
            "Java 是一种面向对象的编程语言，由 Sun Microsystems 公司于 1995 年发布。"
            "Java 的核心理念是'一次编写，到处运行'，通过 Java 虚拟机 (JVM) 实现跨平台。"
            "Java 广泛应用于企业级应用开发、Android 移动开发、大数据处理等场景。"
            "Spring 框架是 Java 生态中最流行的 Web 开发框架。"
        ),
    },
    "doc3": {
        "url": "https://example.com/search-engine",
        "title": "搜索引擎工作原理",
        "text": (
            "搜索引擎是互联网信息检索的核心工具。搜索引擎的工作流程主要包括三个阶段："
            "网络爬取（Crawling）、建立索引（Indexing）和检索排序（Ranking）。"
            "爬虫程序自动访问网页并下载内容，索引器将网页内容构建倒排索引，"
            "检索器根据用户查询在索引中匹配文档并按相关度排序返回结果。"
            "常用的排序算法包括 TF-IDF、BM25 和 PageRank 等。"
            "Google、Bing 和百度是全球最常用的搜索引擎。"
        ),
    },
    "doc4": {
        "url": "https://example.com/machine-learning",
        "title": "机器学习基础教程",
        "text": (
            "机器学习是人工智能的一个分支，它使计算机能够从数据中学习而无需显式编程。"
            "机器学习的主要类型包括监督学习、无监督学习和强化学习。"
            "常见的机器学习算法有线性回归、决策树、支持向量机、神经网络等。"
            "Python 是机器学习领域最流行的编程语言，scikit-learn、TensorFlow 和 PyTorch 是常用的框架。"
            "深度学习是机器学习的子领域，使用多层神经网络处理复杂任务。"
        ),
    },
    "doc5": {
        "url": "https://example.com/web-development",
        "title": "Web 开发技术栈",
        "text": (
            "Web 开发是构建网站和 Web 应用的过程。前端技术包括 HTML、CSS 和 JavaScript。"
            "常用的前端框架有 React、Vue 和 Angular。后端技术包括 Python (Django/Flask)、"
            "Java (Spring)、Node.js 等。数据库分为关系型 (MySQL、PostgreSQL) 和非关系型 (MongoDB、Redis)。"
            "RESTful API 是前后端通信的常用方式。Web 开发还需要关注性能优化、安全性和用户体验。"
        ),
    },
    "doc6": {
        "url": "https://example.com/database",
        "title": "数据库系统概述",
        "text": (
            "数据库是按照数据结构来组织、存储和管理数据的仓库。关系型数据库使用 SQL 语言操作，"
            "支持事务的 ACID 特性：原子性、一致性、隔离性和持久性。"
            "NoSQL 数据库包括文档型 (MongoDB)、键值型 (Redis)、列族型 (HBase) 和图数据库 (Neo4j)。"
            "数据库索引（如 B+ 树索引、哈希索引）可以显著提高查询性能。"
            "倒排索引是全文搜索引擎的核心数据结构。"
        ),
    },
    "doc7": {
        "url": "https://example.com/algorithms",
        "title": "算法与数据结构",
        "text": (
            "算法是解决特定问题的一系列步骤。数据结构是组织和存储数据的方式。"
            "常见的数据结构包括数组、链表、栈、队列、哈希表、树和图。"
            "排序算法有冒泡排序、快速排序、归并排序等。搜索算法有二分查找、深度优先搜索和广度优先搜索。"
            "算法复杂度用大 O 表示法描述时间复杂度和空间复杂度。"
            "好的算法设计能显著提升程序性能。"
        ),
    },
    "doc8": {
        "url": "https://example.com/linux",
        "title": "Linux 操作系统入门",
        "text": (
            "Linux 是一种自由和开放源码的类 Unix 操作系统。Linux 广泛用于服务器、超级计算机和嵌入式设备。"
            "常见的 Linux 发行版有 Ubuntu、CentOS、Debian 和 Arch Linux。"
            "Linux 命令行是系统管理的核心工具，常用命令有 ls、cd、grep、find、chmod 等。"
            "Shell 脚本编程可以自动化日常任务。Docker 容器技术基于 Linux 内核的 cgroup 和 namespace。"
        ),
    },
}


def run_demo(interactive: bool = False):
    """使用内置示例数据运行搜索演示"""
    print("=" * 60)
    print("  纯 Python 搜索引擎 Demo（内置示例数据）")
    print("=" * 60)

    # 1. 构建索引
    print("\n[1/3] 构建索引...")
    idx = InvertedIndex()
    idx.build_from_documents(SAMPLE_DOCS)
    print(f"  索引统计: {idx.stats()}")

    # 2. 创建搜索器
    print("\n[2/3] 初始化搜索器 (BM25 + TF-IDF)")
    searcher = Searcher(idx)

    # 3. 搜索演示
    print("\n[3/3] 搜索演示\n")

    demo_queries = ["Python 编程", "搜索引擎 索引", "机器学习 深度学习", "数据库", "Web 开发"]

    for query in demo_queries:
        _print_results(searcher, query)

    if interactive:
        print("\n" + "=" * 60)
        print("  交互式搜索模式（输入 q 退出）")
        print("=" * 60)
        while True:
            try:
                query = input("\n搜索> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n再见！")
                break
            if query.lower() in ("q", "quit", "exit"):
                print("再见！")
                break
            if not query:
                continue
            _print_results(searcher, query)


def run_crawl(seed_urls: list[str], max_pages: int, max_depth: int,
              save_index: str | None = None, interactive: bool = True):
    """爬取真实网页并构建搜索"""
    from crawler import WebCrawler

    print("=" * 60)
    print("  纯 Python 搜索引擎 - 网络爬取模式")
    print("=" * 60)

    # 1. 爬取
    print("\n[1/3] 爬取网页...")
    crawler = WebCrawler(max_pages=max_pages, max_depth=max_depth, delay=0.5)
    documents = crawler.crawl(seed_urls)

    if not documents:
        print("  未能爬取到任何页面，退出。")
        return

    # 2. 构建索引
    print("\n[2/3] 构建索引...")
    idx = InvertedIndex()
    idx.build_from_documents(documents)
    print(f"  索引统计: {idx.stats()}")

    # 保存索引
    if save_index:
        idx.save(save_index)

    # 3. 搜索
    print("\n[3/3] 搜索")
    searcher = Searcher(idx)

    if interactive:
        print("\n" + "=" * 60)
        print("  交互式搜索模式（输入 q 退出）")
        print("=" * 60)
        while True:
            try:
                query = input("\n搜索> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n再见！")
                break
            if query.lower() in ("q", "quit", "exit"):
                print("再见！")
                break
            if not query:
                continue
            _print_results(searcher, query)
    else:
        # 简单搜索演示
        _print_results(searcher, " ".join(seed_urls))


def run_load(index_file: str, interactive: bool = True):
    """从已保存的索引文件加载并搜索"""
    print("=" * 60)
    print("  纯 Python 搜索引擎 - 加载索引模式")
    print("=" * 60)

    print(f"\n[1/2] 加载索引: {index_file}")
    idx = InvertedIndex.load(index_file)

    print("\n[2/2] 初始化搜索器")
    searcher = Searcher(idx)

    if interactive:
        print("\n" + "=" * 60)
        print("  交互式搜索模式（输入 q 退出）")
        print("=" * 60)
        while True:
            try:
                query = input("\n搜索> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n再见！")
                break
            if query.lower() in ("q", "quit", "exit"):
                print("再见！")
                break
            if not query:
                continue
            _print_results(searcher, query)


def _print_results(searcher: Searcher, query: str):
    """格式化打印搜索结果"""
    print(f"  查询: 「{query}」")
    print(f"  {'─' * 50}")

    # BM25
    results_bm25 = searcher.search_bm25(query, top_k=5)
    print(f"  [BM25 排序] (共 {len(results_bm25)} 条结果)")
    if not results_bm25:
        print(f"    （无匹配结果）")
    for i, r in enumerate(results_bm25, 1):
        print(f"    {i}. [{r.score:.4f}] {r.title}")
        print(f"       URL: {r.url}")
        print(f"       匹配词: {', '.join(r.matched_terms)}")

    # TF-IDF
    results_tfidf = searcher.search_tfidf(query, top_k=5)
    print(f"\n  [TF-IDF 排序] (共 {len(results_tfidf)} 条结果)")
    if not results_tfidf:
        print(f"    （无匹配结果）")
    for i, r in enumerate(results_tfidf, 1):
        print(f"    {i}. [{r.score:.4f}] {r.title}")
        print(f"       URL: {r.url}")
        print(f"       匹配词: {', '.join(r.matched_terms)}")

    print()


# ───────────────────── CLI ─────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="纯 Python 搜索引擎 Demo（爬取 + 索引 + 检索）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py --demo                     # 使用内置数据演示
  python main.py --demo --interactive       # 内置数据 + 交互搜索
  python main.py --crawl https://example.com --max-pages 20
  python main.py --load index.json
        """,
    )

    # 运行模式
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--demo", action="store_true", help="使用内置示例数据运行")
    mode.add_argument("--crawl", nargs="+", metavar="URL", help="从指定 URL 爬取")
    mode.add_argument("--load", metavar="FILE", help="从索引文件加载")

    # 通用选项
    parser.add_argument("--interactive", "-i", action="store_true", help="交互式搜索模式")
    parser.add_argument("--method", choices=["bm25", "tfidf", "both"], default="both",
                        help="排序算法 (默认: both)")

    # 爬取选项
    parser.add_argument("--max-pages", type=int, default=20, help="最大爬取页数 (默认: 20)")
    parser.add_argument("--max-depth", type=int, default=2, help="最大爬取深度 (默认: 2)")
    parser.add_argument("--save-index", metavar="FILE", help="保存索引到文件")

    args = parser.parse_args()

    if args.demo:
        run_demo(interactive=args.interactive)
    elif args.crawl:
        run_crawl(
            seed_urls=args.crawl,
            max_pages=args.max_pages,
            max_depth=args.max_depth,
            save_index=args.save_index,
            interactive=args.interactive,
        )
    elif args.load:
        run_load(args.load, interactive=args.interactive)


if __name__ == "__main__":
    main()
