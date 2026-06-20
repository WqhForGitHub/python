# 07. AI接口服务系统 (FastAPI Demo)

基于 FastAPI 的 AI 接口服务中台 Demo，封装 **LLM 接口**、**异步任务队列**、**请求限流**。

## 功能特性

| 模块 | 说明 |
| --- | --- |
| LLM 接口封装 | mock（默认，无需 key）/ openai，统一 `chat()` 接口可切换 |
| 同步聊天 | `/chat/completions` 实时返回 LLM 回复 |
| 异步任务队列 | `/tasks` 提交后后台 worker 处理，支持失败重试 |
| 请求限流 | 令牌桶算法，按用户隔离，超出返回 429 + Retry-After |
| 优雅降级 | 未配置 API key 时自动降级 mock；调用失败也降级 mock |

## 项目结构

```
07.AI接口服务系统/
├── main.py                # 应用入口（lifespan 启动 worker）
├── config.py              # LLM / 限流 / 队列配置
├── database.py            # 引擎 / Session
├── models.py              # ORM 模型 (AITask)
├── schemas.py             # Pydantic 模型
├── llm.py                 # LLM 客户端封装（mock / openai）
├── limiter.py             # 令牌桶限流器
├── queue.py               # asyncio 任务队列 + worker
├── deps.py                # 依赖项（用户 / 限流）
├── crud/
│   ├── __init__.py
│   └── task.py            # 任务 CRUD + 状态流转
├── routers/
│   ├── __init__.py
│   ├── chat.py            # 同步聊天
│   └── tasks.py           # 异步任务队列
├── requirements.txt
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

> 调用真实 OpenAI 需额外安装：`pip install openai`

### 2. （可选）配置 OpenAI

```bash
set LLM_PROVIDER=openai
set OPENAI_API_KEY=sk-xxx
set OPENAI_MODEL=gpt-3.5-turbo
# 可选：兼容接口
set OPENAI_BASE_URL=https://api.openai.com/v1
```

> 未配置时默认使用 mock provider，返回占位回复，便于离线演示。

### 3. 启动服务

```bash
cd "demo/07.AI接口服务系统"
uvicorn main:app --reload
```

## 接口一览

> 接口需 `X-User-Id` 请求头标识用户。

### 同步聊天 `/chat`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/chat/completions` | 同步聊天（实时返回，受限流） |
| GET | `/chat/rate-limit` | 查询当前限流状态 |

### 异步任务 `/tasks`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/tasks/` | 提交异步任务（立即返回 task_id） |
| GET | `/tasks/` | 我的任务列表 |
| GET | `/tasks/{task_id}` | 查询任务状态与结果 |
| GET | `/tasks/{task_id}/wait` | 轮询等待完成（最多 30 秒） |

## 使用示例

### 1. 同步聊天

```bash
curl -X POST http://127.0.0.1:8000/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 1" \
  -d '{"messages":[{"role":"user","content":"你好"}]}'
```

### 2. 提交异步任务

```bash
curl -X POST http://127.0.0.1:8000/tasks/ \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 1" \
  -d '{"prompt":"写一首关于秋天的诗"}'
```

返回：

```json
{"task_id":"abc123...","status":"pending", ...}
```

### 3. 轮询等待结果

```bash
curl http://127.0.0.1:8000/tasks/abc123.../wait -H "X-User-Id: 1"
```

### 4. 触发限流（连续快速请求）

```bash
# 默认容量 5，连续 6 次将 429
for i in 1 2 3 4 5 6; do
  curl http://127.0.0.1:8000/chat/rate-limit -H "X-User-Id: 1"
done
```

## 技术要点

- **LLM 接口抽象**：`chat()` 统一入口，mock / openai 双实现，按配置选择
- **优雅降级**：无 key 用 mock；openai 调用失败也降级 mock，保证 Demo 可用
- **令牌桶限流**：`RateLimiter` 按 user_id 维护独立桶，线程安全；429 携带 `Retry-After`
- **异步任务队列**：`asyncio.Queue` + N 个 worker 协程，lifespan 管理
- **状态流转**：pending -> running -> succeeded/failed，失败重试（retrying 回 pending）
- **任务持久化**：任务记录落库，重启不丢失（但运行中的需重新入队）

## 扩展思路

- 接入 Redis 实现分布式限流（如 redis-cell）
- 任务队列替换为 Celery / RQ / Dramatiq
- 流式响应（SSE / WebSocket）逐 token 返回
- 接入更多模型供应商（Anthropic / 通义千问）
- 任务优先级 / 取消
- token 用量统计与计费
