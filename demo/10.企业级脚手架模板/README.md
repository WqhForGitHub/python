# 10. 企业级脚手架模板 (FastAPI Demo)

生产级 FastAPI 脚手架模板，采用 **分层架构（api / service / repository / model）**，集成 **PostgreSQL + Redis + JWT + RBAC + Docker**，可作为真实项目起点。

## 功能特性

| 模块 | 说明 |
| --- | --- |
| 分层架构 | api -> service -> repository -> model，职责清晰，易于测试 |
| 异步数据库 | PostgreSQL（asyncpg），无 PG 时可降级 SQLite（aiosqlite） |
| Redis | 可选，异步客户端，连接失败自动跳过 |
| JWT + RBAC | 用户 - 角色 - 权限三级，依赖工厂式权限校验 |
| 统一响应 | `{code, message, data}` 包装 + 全局异常处理 |
| 版本化路由 | `/api/v1/*`，便于后续演进 |
| 应用工厂 | `create_app()` 工厂模式，便于测试与多环境 |
| 配置管理 | pydantic-settings，支持 .env / 环境变量 |
| Docker 部署 | 多阶段构建 Dockerfile + docker-compose（PG + Redis + API） |
| 测试示例 | pytest + httpx ASGITransport，SQLite 内存库 |

## 项目结构

```
10.企业级脚手架模板/
├── app/
│   ├── __init__.py
│   ├── main.py                # 应用工厂 + lifespan
│   ├── initial_data.py        # 初始化权限/角色/管理员
│   ├── core/                  # 基础设施
│   │   ├── config.py          # Settings（pydantic-settings）
│   │   ├── database.py        # 异步引擎 / Session
│   │   ├── redis.py           # Redis 客户端
│   │   ├── security.py        # 密码哈希 + JWT
│   │   ├── exceptions.py      # 自定义异常 + 处理器
│   ├── models/                # ORM 模型层
│   │   ├── base.py            # Base + TimestampMixin + IDMixin
│   │   ├── user.py            # User + user_roles
│   │   └── role.py            # Role / Permission
│   ├── schemas/               # Pydantic 模型
│   │   ├── common.py          # 统一响应 / Token
│   │   ├── auth.py            # 注册 / 登录
│   │   └── user.py            # 用户读写
│   ├── repositories/          # 数据访问层
│   │   ├── base.py            # 泛型 BaseRepository
│   │   └── user.py            # User/Role/Permission 仓库
│   ├── services/              # 业务逻辑层
│   │   ├── auth_service.py    # 注册/登录/刷新
│   │   └── user_service.py    # 用户 CRUD + 角色
│   └── api/                   # HTTP 接口层
│       ├── deps.py            # 当前用户 / RBAC 依赖
│       └── v1/
│           ├── router.py      # v1 路由聚合
│           ├── auth.py        # /api/v1/auth
│           └── users.py       # /api/v1/users
├── tests/
│   ├── conftest.py            # pytest fixtures（内存 SQLite）
│   └── test_auth.py           # 认证与 RBAC 集成测试
├── Dockerfile                 # 多阶段构建
├── docker-compose.yml         # PG + Redis + API
├── .dockerignore
├── .env.example
├── requirements.txt
└── README.md
```

## 快速开始

### 方式一：Docker Compose（推荐，一键拉起 PG + Redis + API）

```bash
cd "demo/10.企业级脚手架模板"
docker compose up -d --build
```

访问 http://127.0.0.1:8000/docs ，默认账号 `admin / Admin123456`。

### 方式二：本地运行（SQLite 降级，无需 PG/Redis）

```bash
pip install -r requirements.txt
cd "demo/10.企业级脚手架模板"
# 使用 SQLite，无需外部依赖
set DATABASE_URL=sqlite+aiosqlite:///./scaffold.db
uvicorn app.main:app --reload
```

> 不设 `DATABASE_URL` 时默认连 PostgreSQL；本地无 PG 请按上面设置 SQLite。

### 方式三：本地 + 真实 PostgreSQL / Redis

```bash
docker run -d -p 5432:5432 -e POSTGRES_USER=app -e POSTGRES_PASSWORD=app -e POSTGRES_DB=scaffold postgres:16-alpine
docker run -d -p 6379:6379 redis:7-alpine
cp .env.example .env  # 按需修改
uvicorn app.main:app --reload
```

## 接口一览（/api/v1）

### 认证 `/auth`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/auth/register` | 注册 |
| POST | `/auth/login` | 登录（表单，兼容 Swagger Authorize） |
| POST | `/auth/refresh` | 刷新令牌 |
| GET | `/auth/me` | 当前登录用户 |
| POST | `/auth/logout` | 登出 |

### 用户管理 `/users`

| 方法 | 路径 | 所需权限 |
| --- | --- | --- |
| GET | `/users/` | `user:read` |
| GET | `/users/me` | 仅登录 |
| GET | `/users/{id}` | `user:read` |
| PUT | `/users/{id}` | `user:write` |
| DELETE | `/users/{id}` | `user:delete` |
| PUT | `/users/{id}/roles` | `user:assign_role` |

## 使用示例

### 1. 登录

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -d "username=admin&password=Admin123456"
```

### 2. 访问用户列表

```bash
curl http://127.0.0.1:8000/api/v1/users/ \
  -H "Authorization: Bearer <token>"
```

### 3. 运行测试

```bash
pip install pytest httpx pytest-asyncio
pytest -v
```

## 技术要点

- **分层架构**：API（路由 / 参数校验）-> Service（业务逻辑）-> Repository（数据访问）-> Model（ORM），各层单向依赖
- **泛型 Repository**：`BaseRepository[ModelT]` 提供通用 CRUD，子类只写特有查询
- **应用工厂**：`create_app()` 便于测试隔离与多实例部署
- **pydantic-settings**：类型安全配置，`.env` + 环境变量双来源，`@lru_cache` 单例
- **统一异常**：`AppException` 体系 + 全局 handler，统一 `{code,message}` 响应
- **RBAC 依赖工厂**：`require_permissions("user:read")` 声明式权限，superuser 直通
- **多阶段 Docker 构建**：builder 阶段编译依赖，运行镜像仅含运行时，体积小
- **Docker Compose**：PG / Redis 健康检查 + depends_on condition，API 待依赖就绪再启动
- **测试隔离**：`ASGITransport` + SQLite 内存库，每个测试独立建表/清理

## 扩展思路

- 引入 Alembic 管理数据库迁移
- refresh token 入库（Redis）支持吊销 / 单点登出
- 接入 OpenTelemetry 链路追踪 + Prometheus 指标（见 Demo 09）
- 接入结构化日志（structlog / loguru）
- API 限流（见 Demo 07）
- CI/CD：GitHub Actions 自动测试 + 构建镜像
- 拆分微服务（见 Demo 08）
