# 搜索引擎（爬取 + 索引 + 检索）

纯 Python 标准库实现，包含搜索引擎的三大核心模块：

- **Crawler**：基于 `urllib` 的广度优先爬虫，自带 HTML 解析（`html.parser`），支持同域名限制
- **Indexer**：倒排索引 + TF-IDF；用 `pickle` 持久化到本地
- **Searcher**：多词查询、TF-IDF 排序、片段高亮 `[关键词]`

## 用法

```bash
# 1) 不联网，跑内置文档示例
python search_engine.py demo

# 2) 联网爬一个站点（同域名）
python search_engine.py crawl https://example.com --max=30 --same-host

# 3) 抓完后构建索引
python search_engine.py index

# 4) 搜索
python search_engine.py search "Python 爬虫"
```

## 数据目录

抓取页面 / 索引会保存在脚本同级目录下的 `se_data/`：

```
se_data/
├── pages/        # 每个 .pkl 是一篇页面（id, url, title, text）
├── index.pkl     # 倒排索引：term -> {doc_id: tf}
└── docs.pkl      # 文档元信息：doc_id -> {url, title, length, snippet}
```

## 设计要点

- 分词器对英文按非字母数字切分、对 CJK 做单字切分；带一份精简停用词表
- 排名公式：`score(d, q) = Σ_{t∈q} (tf_{t,d} / |d|) * idf_t`，`idf = log((N+1)/(df+1))+1`
- HTML 解析使用标准库 `html.parser`，跳过 `<script>/<style>/<noscript>`
- 没有任何第三方依赖
