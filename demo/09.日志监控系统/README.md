# 09. 日志监控系统 (FastAPI Demo)

基于 FastAPI 的运维类日志监控系统 Demo，包含 **API 日志收集**、**请求追踪**、**性能统计**、**Prometheus 指标**。

## 功能特性

| 模块 | 说明 |
| --- | --- |
| API 日志收集 | 中间件记录每次请求（method/path/status/duration/ip/UA）并落库 |
| 请求追踪 | 每个请求生成 / 透传 `X-Request-ID`，响应头回写，便于跨服务追踪 |
| 性能统计 | 总数 / 成功率 / 平均 / P95 / 最大耗时，按接口路径聚合 |
| Prometheus 指标 | `/metrics` 端点暴露请求计数、耗时直方图、在处理数、错误数 |
| 慢请求告警 | 超过阈值（默认 1s）打 WARN 日志 |
| 路径归一化 | 数字 ID 替换为 `{id}`，避免指标基数爆炸 |
| 日志独立 Session | 日志写入用独立 DB Session，不影响业务事务 |

## 项目结构

```
09.日志监控系统/
├── main.py                # 应用入口 + 中间件注册
├── config.py              # 慢请求阈值 / 请求头名
├── database.py            # 引擎 / Session
├── models.py              # ORM 模型 (RequestLog)
├── schemas.py             # Pydantic 模型
├── metrics.py             # Prometheus 指标定义
├── middleware.py          # 请求日志 + 追踪中间件
├── crud/
│   ├── __init__.py
│   └── log.py             # 日志查询 + 性能统计
├── routers/
│   ├── __init__.py
│   ├── logs.py            # 日志查询 / 统计 / metrics 端点
│   └── demo.py            # 示例业务接口（产生日志）
├── requirements.txt
└── README.md
```

## 快速开始

```bash
pip install -r requirements.txt
cd "demo/09.日志监控系统"
uvicorn main:app --reload
```

### 产生一些日志

```bash
# 多次访问示例接口（含正常 / 慢 / 错误）
curl http://127.0.0.1:8000/demo/ok
curl http://127.0.0.1:8000/demo/slow
curl http://127.0.0.1:8000/demo/random
curl http://127.0.0.1:8000/demo/error
curl http://127.0.0.1:8000/demo/echo/123
```

## 接口一览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/logs` | 请求日志列表（支持 method/status/path/since 筛选） |
| GET | `/logs/{request_id}` | 按 request_id 查询详情 |
| GET | `/stats/summary` | 性能汇总（总数/成功率/平均/P95/最大） |
| GET | `/stats/paths` | 按接口路径聚合统计 |
| GET | `/metrics` | **Prometheus 指标端点** |
| GET | `/demo/ok` | 正常请求（200） |
| GET | `/demo/slow` | 慢请求（~1.5s） |
| GET | `/demo/random` | 随机耗时（0~2s） |
| GET | `/demo/error` | 触发 500 |
| GET | `/demo/echo/{id}` | 带路径参数 |

## 使用示例

### 1. 携带自定义 request_id

```bash
curl -H "X-Request-ID: my-trace-001" http://127.0.0.1:8000/demo/ok -i
# 响应头包含 X-Request-ID: my-trace-001
```

```bash
curl http://127.0.0.1:8000/logs/my-trace-001
```

### 2. 性能汇总

```bash
curl http://127.0.0.1:8000/stats/summary?since_minutes=60
```

```json
{
  "total": 42, "success": 38, "client_error": 3, "server_error": 1,
  "avg_duration_ms": 156.3, "p95_duration_ms": 1500.0, "max_duration_ms": 1502
}
```

### 3. Prometheus 指标

```bash
curl http://127.0.0.1:8000/metrics
```

```
# HELP http_requests_total HTTP 请求总数
# TYPE http_requests_total counter
http_requests_total{method="GET",path="/demo/ok",status="200"} 5.0
# HELP http_request_duration_ms HTTP 请求耗时（毫秒）
# TYPE http_request_duration_ms histogram
http_request_duration_ms_bucket{method="GET",path="/demo/slow",le="1000"} 0.0
http_request_duration_ms_bucket{method="GET",path="/demo/slow",le="2500"} 1.0
...
```

### 4. 接入 Prometheus + Grafana

`prometheus.yml` 示例：

```yaml
scrape_configs:
  - job_name: fastapi-logs-demo
    metrics_path: /metrics
    static_configs:
      - targets: ["host.docker.internal:8000"]
```

## 技术要点

- **请求追踪**：`X-Request-ID` 透传 + 回写，串联一次请求的全链路日志
- **中间件落库**：`BaseHTTPMiddleware` 捕获 status / duration / 异常，独立 Session 写入
- **Prometheus 指标**：Counter（计数）/ Histogram（耗时分布）/ Gauge（在处理数）
- **路径归一化**：`/demo/echo/123` -> `/demo/echo/{id}`，控制指标 label 基数
- **P95 计算**：取出窗口内全部耗时排序后取第 95 百分位（Demo 实现，大数据量应改用近似算法）
- **慢请求阈值**：超过 `SLOW_REQUEST_THRESHOLD` 打 WARN，便于运维定位
- **指标端点豁免**：`/metrics` 自身不计入指标，避免自引用

## 扩展思路

- 引入 OpenTelemetry 标准化分布式追踪
- 日志异步写入（队列 + 批量落库）避免阻塞请求
- 接入 ELK / Loki 进行日志检索
- P95 改用 t-digest / HDR Histogram 近似算法
- 接入告警规则（Prometheus Alertmanager）
- 链路追踪透传到下游服务（见 Demo 08 微服务）
