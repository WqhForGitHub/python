"""FastAPI 应用入口。

启动方式：
    uvicorn main:app --reload

日志监控系统 Demo：
- API 日志收集（中间件落库）
- 请求追踪（X-Request-ID）
- 性能统计（汇总 / 按接口）
- Prometheus 指标端点
"""
from fastapi import FastAPI

import models
from database import engine
from middleware import RequestLoggingMiddleware
from routers import demo, logs

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="日志监控系统",
    description=(
        "基于 FastAPI 的运维类日志监控系统 Demo。\n\n"
        "## 功能特性\n"
        "- **API 日志收集**：中间件记录每次请求（method/path/status/duration/ip）\n"
        "- **请求追踪**：每个请求生成 / 透传 `X-Request-ID`，跨服务链路追踪\n"
        "- **性能统计**：总数 / 成功率 / 平均 / P95 / 最大耗时，按接口聚合\n"
        "- **Prometheus 指标**：`/metrics` 端点供 Prometheus 抓取\n"
        "- **慢请求告警**：超过阈值打 WARN 日志\n\n"
        "## 示例\n"
        "访问 `/demo/ok`、`/demo/slow`、`/demo/error` 产生日志，"
        "再查看 `/logs`、`/stats/summary`、`/metrics`。"
    ),
    version="1.0.0",
)

# 注册日志中间件
app.add_middleware(RequestLoggingMiddleware)


@app.get("/", tags=["默认"], summary="欢迎页")
def root():
    return {
        "message": "欢迎使用日志监控系统",
        "docs": "/docs",
        "metrics": "/metrics",
        "logs": "/logs",
        "stats": "/stats/summary",
    }


app.include_router(logs.router)
app.include_router(demo.router)
