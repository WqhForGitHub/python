# PyScrap —— 类 Scrapy 的迷你爬虫框架

纯 Python 标准库实现，复刻 Scrapy 的核心抽象与执行模型。

## 核心组件

| 组件 | 作用 |
|------|------|
| `Spider`   | 用户编写的爬虫；定义 `start_urls` + `parse()` |
| `Request`  | 描述一次请求（url、method、callback、meta） |
| `Response` | 响应对象，提供 `.text` / `.css()` / `.follow()` |
| `Selector` | 极简 CSS 选择器：`tag` / `.class` / `#id` |
| `Scheduler`| 请求队列 + URL 去重 |
| `Downloader` | 用 `urllib` 下载，支持中间件 |
| `Pipeline` | 处理 item（去重、写文件、打印） |
| `Engine`   | 主循环：调度 → 并发下载 → 解析 → 分发 |

## 用法

```bash
# 1) 跑内置示例（不联网，使用 local:// 内置 HTML）
python pyscrap.py

# 2) 抓任意 URL 的所有链接
python pyscrap.py https://example.com
```

抓到的 item 会同时打印到控制台 **并** 写入 `items.jsonl`。

## 写一个自定义 Spider

```python
class MySpider(Spider):
    name = "my"
    start_urls = ["https://example.com"]

    def parse(self, response):
        for h in response.css("h1"):
            yield {"title": h.get()}
        for a in response.css("a"):
            href = a.get("href")
            if href:
                yield response.follow(href, callback=self.parse)
```

## 中间件 / 管道

- `DefaultHeadersMiddleware`：注入默认 UA
- 自定义 `DownloaderMiddleware` 重写 `process_request / process_response`
- 内置 `PrintPipeline / DedupPipeline / JsonLinesPipeline`

## 与真 Scrapy 的差异

- 没有 Twisted / asyncio：使用线程池实现并发下载
- 没有 XPath：选择器只支持极简的 tag/class/id
- 没有 settings 文件 / 项目结构：单文件即可运行
