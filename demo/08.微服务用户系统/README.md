# 08. 微服务用户系统 (FastAPI Demo)

基于纯 FastAPI 实现的微服务用户系统 Demo，演示 **服务注册 / 发现、反向代理网关、服务间调用、鉴权聚合**。

## 架构

```
                      ┌──────────────────────┐
   客户端  ─────────► │   api-gateway :8000   │  注册中心 + 反向代理 + 鉴权
                      └──────────┬───────────┘
                          注册/心跳 │ 转发
              ┌────────────────────┼────────────────────┐
              ▼                                         ▼
   ┌────────────────────┐                    ┌────────────────────┐
   │  auth-service :8001 │  ── 调用 ──►       │  user-service :8002 │
   │  JWT 签发 / 校验     │   校验凭据          │  用户 CRUD           │
   └────────────────────┘                    └────────────────────┘
```

## 功能特性

| 模块 | 说明 |
| --- | --- |
| 服务注册中心 | 网关内置，服务启动时注册，定期心跳，超时下线 |
| 服务发现 | 网关从注册表选择健康实例转发（轮询负载均衡） |
| 反向代理 | `/api/auth/*` -> auth-service，`/api/users/*` -> user-service |
| 鉴权网关 | 受保护接口先调 auth-service 校验 token |
| 服务间调用 | auth-service 登录时远程调用 user-service 校验凭据 |
| 服务聚合 | `/api/me` 串联 auth + user 两个服务返回完整用户信息 |
| 健康检查 | 各服务提供 `/health`，注册表基于心跳判定存活 |

## 项目结构

```
08.微服务用户系统/
├── shared/                    # 跨服务共享代码
│   ├── __init__.py
│   ├── registry.py            # 服务注册表（网关内运行）
│   ├── client.py              # 注册/心跳/注销/调用辅助
│   └── models.py              # 共享 Pydantic 模型
├── api-gateway/               # 网关 + 注册中心
│   ├── main.py
│   ├── config.py
│   └── requirements.txt
├── auth-service/              # 认证服务
│   ├── main.py
│   ├── config.py
│   ├── security.py            # JWT 编解码
│   └── requirements.txt
├── user-service/              # 用户服务
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── crud.py
│   └── requirements.txt
├── start_all.py               # 一键启动全部服务
└── README.md
```

## 快速开始

### 1. 安装依赖（每个服务目录均需）

```bash
cd "demo/08.微服务用户系统"
pip install -r api-gateway/requirements.txt
pip install -r auth-service/requirements.txt
pip install -r user-service/requirements.txt
```

### 2. 启动（三个终端分别启动，注意顺序）

```bash
# 终端 1：网关（先启动）
cd api-gateway
uvicorn main:app --reload --port 8000 --host 0.0.0.0

# 终端 2：认证服务
cd auth-service
uvicorn main:app --reload --port 8001 --host 0.0.0.0

# 终端 3：用户服务
cd user-service
uvicorn main:app --reload --port 8002 --host 0.0.0.0
```

或一键启动：

```bash
python start_all.py
```

### 3. 访问

| 地址 | 说明 |
| --- | --- |
| http://127.0.0.1:8000/docs | 网关 Swagger |
| http://127.0.0.1:8000/registry/services | 已注册服务列表 |
| http://127.0.0.1:8001/docs | auth-service 文档 |
| http://127.0.0.1:8002/docs | user-service 文档 |

## 接口一览

### 网关 `/registry`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/registry/register` | 服务注册 |
| POST | `/registry/heartbeat` | 服务心跳 |
| POST | `/registry/deregister` | 服务注销 |
| GET | `/registry/services` | 已注册服务列表（含健康状态） |

### 网关代理 `/api`

| 方法 | 路径 | 转发目标 | 鉴权 |
| --- | --- | --- | --- |
| POST | `/api/auth/login` | auth-service /login | 无 |
| GET | `/api/auth/verify` | auth-service /verify | 无 |
| GET | `/api/users` | user-service /users | 需 token |
| GET | `/api/users/{id}` | user-service /users/{id} | 需 token |
| POST | `/api/users` | user-service /users | 需 token |
| GET | `/api/me` | 聚合 auth + user | 需 token |

## 使用示例

### 1. 查看注册的服务

```bash
curl http://127.0.0.1:8000/registry/services
```

### 2. 登录获取 token（默认账号 alice / Alice123456）

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"Alice123456"}'
```

### 3. 携带 token 访问用户列表（经网关鉴权）

```bash
curl http://127.0.0.1:8000/api/users \
  -H "Authorization: Bearer <token>"
```

### 4. 聚合接口 /api/me（串联两个服务）

```bash
curl http://127.0.0.1:8000/api/me -H "Authorization: Bearer <token>"
```

返回包含 `verified_by: auth-service` 与 `fetched_from: user-service`。

## 技术要点

- **服务注册思想**：服务启动注册 + 周期心跳 + TTL 健康检查 + 优雅注销
- **进程内注册表**：`ServiceRegistry` 用字典 + 锁实现，演示注册发现机制；生产用 Consul/etcd
- **轮询负载均衡**：`discover()` 在多个健康实例间轮询选择
- **反向代理**：网关用 httpx 转发原始请求 / 响应，剥离 hop-by-hop 头
- **鉴权网关**：受保护路径先调 auth-service `/verify` 校验，再转发到业务服务
- **服务间调用**：auth-service 登录时调 user-service `/internal/verify` 校验凭据
- **服务聚合**：`/api/me` 一次请求串联两个服务，对客户端透明
- **共享代码包**：`shared/` 跨服务复用模型与客户端，通过 sys.path 注入

## 扩展思路

- 注册中心独立为单独服务（Consul / Nacos / etcd）
- 引入配置中心统一下发配置
- 网关支持限流 / 熔断 / 重试（resilience4j 思想）
- 服务间通信改为 gRPC / 消息队列
- 引入链路追踪（OpenTelemetry / Jaeger，见 Demo 09）
- Docker Compose 编排多服务（见 Demo 10）
- 服务实例水平扩展 + 一致性哈希负载均衡
