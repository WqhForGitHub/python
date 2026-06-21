"""Prometheus 指标定义。

暴露 /metrics 端点供 Prometheus 抓取。
"""

from prometheus_client import Counter, Histogram, generate_latest

# 请求总数（按 method / path / status）
REQUEST_COUNT = Counter(
    "http_requests_total",
    "HTTP 请求总数",
    ["method", "path", "status"],
)

# 请求耗时直方图（毫秒）
REQUEST_LATENCY = Histogram(
    "http_request_duration_ms",
    "HTTP 请求耗时（毫秒）",
    ["method", "path"],
    buckets=(5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000),
)

# 在处理中的请求数（Gauge）
from prometheus_client import Gauge

REQUEST_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "当前处理中的 HTTP 请求数",
    ["method"],
)

# 业务异常计数
ERROR_COUNT = Counter(
    "http_errors_total",
    "HTTP 错误（5xx）总数",
    ["method", "path"],
)


def record_request(method: str, path: str, status: int, duration_ms: float) -> None:
    REQUEST_COUNT.labels(method=method, path=path, status=str(status)).inc()
    REQUEST_LATENCY.labels(method=method, path=path).observe(duration_ms)
    if status >= 500:
        ERROR_COUNT.labels(method=method, path=path).inc()


def render_metrics() -> str:
    """生成 Prometheus 文本格式指标。"""
    return generate_latest().decode("utf-8")
