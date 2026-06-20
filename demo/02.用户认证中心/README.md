# 02. 用户认证中心 (FastAPI Demo)

基于纯 FastAPI 实现的用户认证中心 Demo，包含 **JWT 登录 / 注册**、**Refresh Token 令牌轮转**、**RBAC 权限控制** 三大核心能力。

## 功能特性

| 模块 | 说明 |
| --- | --- |
| JWT 登录 / 注册 | 基于 access_token 的无状态鉴权，密码使用 bcrypt 哈希存储 |
| Refresh Token | 长效刷新令牌，支持**令牌轮转**（refresh 时吊销旧令牌）与**登出吊销** |
| RBAC 权限控制 | 用户 - 角色 - 权限三级模型，接口级细粒度权限校验 |
| 统一依赖注入 | `get_current_user` / `require_permissions` / `require_roles` 复用便捷 |
| Swagger 文档 | 内置 `/docs`，支持点击 "Authorize" 按钮一键登录调试 |
| SQLite + SQLAlchemy | 轻量级持久化，首次启动自动建表并初始化默认数据 |

## 项目结构

```
02.用户认证中心/
├── main.py                # FastAPI 应用入口
├── config.py              # 配置（密钥、Token 有效期、初始管理员）
├── database.py            # 数据库引擎 / Session
├── models.py              # ORM 模型 (User / Role / Permission / RefreshToken)
├── schemas.py             # Pydantic 请求/响应模型
├── security.py            # 密码哈希 + JWT 编解码工具
├── deps.py                # 依赖项（当前用户、权限/角色校验工厂）
├── initial_data.py        # 初始化默认权限/角色/管理员
├── crud/
│   ├── __init__.py
│   ├── user.py            # 用户 CRUD + RBAC 辅助
│   ├── role.py            # 角色 CRUD
│   ├── permission.py      # 权限 CRUD
│   └── token.py           # 刷新令牌 CRUD（吊销/轮转/清理）
├── routers/
│   ├── __init__.py
│   ├── auth.py            # 注册/登录/刷新/登出/当前用户
│   ├── users.py           # 用户管理（需权限）
│   ├── roles.py           # 角色与角色权限管理（需权限）
│   ├── permissions.py     # 权限管理（需权限）
│   └── demo.py            # 受保护资源示例（演示三级访问控制）
├── requirements.txt
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 进入项目目录

```bash
cd "demo/02.用户认证中心"
```

### 3. 启动开发服务器

```bash
uvicorn main:app --reload
```

首次启动时会自动生成 `auth_demo.db`，建表，并写入默认权限、角色与账号。

### 4. 访问

| 地址 | 说明 |
| --- | --- |
| http://127.0.0.1:8000/ | 根路径欢迎页 |
| http://127.0.0.1:8000/docs | Swagger UI（可点击 Authorize 登录调试） |
| http://127.0.0.1:8000/redoc | ReDoc 文档 |

## 默认账号

| 用户名 | 密码 | 角色 | 权限 |
| --- | --- | --- | --- |
| `admin` | `Admin123456` | admin | 全部权限 |
| `alice` | `Alice123456` | user | 仅 `article:read` / `article:write` |

> 管理员账号可通过环境变量覆盖（见 `config.py`）。

## RBAC 模型

```
User  <--多对多-->  Role  <--多对多-->  Permission
```

- **Permission**：以 `资源:操作` 形式编码，如 `user:read`、`article:write`
- **Role**：角色的集合，如 `admin`、`user`、`editor`
- **User**：通过角色间接获得权限

### 预置权限

| 编码 | 名称 |
| --- | --- |
| `user:read` | 查看用户 |
| `user:write` | 编辑用户 |
| `user:delete` | 删除用户 |
| `user:assign_role` | 分配角色 |
| `role:read` | 查看角色 |
| `role:write` | 编辑角色 |
| `permission:manage` | 管理权限 |
| `role:delete` | 删除角色 |
| `article:read` | 查看文章（示例） |
| `article:write` | 编辑文章（示例） |

## 接口一览

### 认证接口 `/auth`

| 方法 | 路径 | 说明 | 鉴权 |
| --- | --- | --- | --- |
| POST | `/auth/register` | 注册（默认分配 user 角色） | 无 |
| POST | `/auth/login` | 登录，返回 access + refresh token | 无 |
| POST | `/auth/refresh` | 刷新令牌（轮转） | 无（需 refresh_token） |
| POST | `/auth/logout` | 登出（吊销 refresh_token） | 无（需 refresh_token） |
| GET | `/auth/me` | 获取当前登录用户 | access_token |

### 用户管理 `/users`

| 方法 | 路径 | 所需权限 |
| --- | --- | --- |
| GET | `/users/` | `user:read` |
| GET | `/users/{id}` | `user:read` |
| PUT | `/users/{id}` | `user:write` |
| DELETE | `/users/{id}` | `user:delete` |
| PUT | `/users/{id}/roles` | `user:assign_role` |

### 角色管理 `/roles`

| 方法 | 路径 | 所需权限 |
| --- | --- | --- |
| GET | `/roles/` | `role:read` |
| POST | `/roles/` | `role:write` |
| GET | `/roles/{id}` | `role:read` |
| PUT | `/roles/{id}` | `role:write` |
| DELETE | `/roles/{id}` | `role:delete` |
| PUT | `/roles/{id}/permissions` | `role:write` |

### 权限管理 `/permissions`

| 方法 | 路径 | 所需权限 |
| --- | --- | --- |
| GET | `/permissions/` | `permission:manage` |
| POST | `/permissions/` | `permission:manage` |

### 示例受保护资源 `/demo`

| 方法 | 路径 | 鉴权级别 |
| --- | --- | --- |
| GET | `/demo/public` | 公开 |
| GET | `/demo/profile` | 已登录即可 |
| GET | `/demo/read` | `article:read` |
| POST | `/demo/write` | `article:write` |

## 使用示例

### 1. 登录获取令牌

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=Admin123456"
```

响应：

```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 2. 携带令牌访问受保护接口

```bash
curl http://127.0.0.1:8000/users/ \
  -H "Authorization: Bearer <access_token>"
```

### 3. 刷新令牌（轮转）

```bash
curl -X POST http://127.0.0.1:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
```

> 旧的 refresh_token 会被立即吊销，返回全新的令牌对。

### 4. 登出

```bash
curl -X POST http://127.0.0.1:8000/auth/logout \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
```

### 5. RBAC 权限校验示例

以 `alice`（仅有 article 权限）登录后访问用户列表，将返回 403：

```bash
curl http://127.0.0.1:8000/users/ \
  -H "Authorization: Bearer <alice_access_token>"
# {"detail":"权限不足，需要以下权限之一：user:read"}
```

而访问 `/demo/read` 则成功：

```bash
curl http://127.0.0.1:8000/demo/read \
  -H "Authorization: Bearer <alice_access_token>"
# {"message":"你拥有 article:read 权限，可以查看文章"}
```

## 技术要点

- **双令牌机制**：access_token 短期有效（30 分钟），refresh_token 长期有效（7 天），降低令牌泄露风险
- **令牌轮转（Rotation）**：每次刷新都吊销旧 refresh_token 并签发新对，防止重放攻击
- **令牌吊销**：refresh_token 持久化于数据库（仅存哈希），登出即可吊销
- **RBAC 依赖工厂**：`require_permissions("user:read")` 一行声明接口所需权限，复用性强
- **密码安全**：bcrypt 哈希存储，永不落库明文
- **OAuth2PasswordBearer**：登录接口兼容表单，Swagger "Authorize" 按钮可一键登录
- **环境变量配置**：密钥、有效期、管理员账号均可通过环境变量覆盖

## 扩展思路

- 接入 Redis 存储 refresh_token，提升吊销性能
- access_token 也入黑名单，支持「立即踢下线」
- 增加登录失败次数限制与账号锁定
- 接入 MySQL / PostgreSQL，使用 Alembic 管理迁移
- 增加接口级审计日志
- 增加单元测试（pytest + httpx）
