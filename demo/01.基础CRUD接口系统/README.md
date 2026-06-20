# 01. 基础CRUD接口系统 (FastAPI Demo)

一个使用 FastAPI 实现的基础 CRUD 接口系统 Demo，包含 **用户 (User)** 与 **文章 (Article)** 两个资源的增删改查接口，使用 Pydantic 进行请求体校验，FastAPI 自动生成 Swagger / ReDoc 文档。

## 功能特性

| 模块 | 说明 |
| --- | --- |
| 用户 CRUD | 创建 / 查询列表 / 查询详情 / 更新 / 删除 |
| 文章 CRUD | 创建 / 查询列表 / 查询详情 / 更新 / 删除，关联作者 |
| Pydantic 校验 | 请求体、响应模型字段类型与约束校验（邮箱、长度、正则等） |
| Swagger 自动文档 | FastAPI 内置 `/docs` 与 `/redoc` |
| SQLite + SQLAlchemy | 轻量级持久化，ORM 模型清晰 |
| 统一异常处理 | 资源不存在返回 404，校验失败自动 422 |

## 项目结构

```
01.基础CRUD接口系统/
├── main.py                # FastAPI 应用入口
├── database.py            # 数据库引擎 / Session
├── models.py              # SQLAlchemy ORM 模型 (User, Article)
├── schemas.py             # Pydantic 模型 (请求/响应)
├── crud/
│   ├── __init__.py
│   ├── user.py            # 用户 CRUD 操作
│   └── article.py         # 文章 CRUD 操作
├── routers/
│   ├── __init__.py
│   ├── users.py           # 用户路由
│   └── articles.py        # 文章路由
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
cd "demo/01.基础CRUD接口系统"
```

### 3. 启动开发服务器

```bash
uvicorn main:app --reload
```

首次启动时会自动在项目根目录生成 `crud_demo.db`（SQLite），并建表。

### 4. 访问

| 地址 | 说明 |
| --- | --- |
| http://127.0.0.1:8000/ | 根路径欢迎页 |
| http://127.0.0.1:8000/docs | Swagger UI 交互文档 |
| http://127.0.0.1:8000/redoc | ReDoc 文档 |
| http://127.0.0.1:8000/openapi.json | OpenAPI Schema |

## 接口一览

### 用户接口 `/users`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/users/` | 创建用户 |
| GET | `/users/` | 用户列表（支持 skip / limit 分页） |
| GET | `/users/{user_id}` | 用户详情 |
| PUT | `/users/{user_id}` | 更新用户（全量） |
| DELETE | `/users/{user_id}` | 删除用户 |

### 文章接口 `/articles`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/articles/` | 创建文章（需指定 author_id） |
| GET | `/articles/` | 文章列表（支持 skip / limit 分页） |
| GET | `/articles/{article_id}` | 文章详情 |
| PUT | `/articles/{article_id}` | 更新文章 |
| DELETE | `/articles/{article_id}` | 删除文章 |

## 示例请求

### 创建用户

```bash
curl -X POST http://127.0.0.1:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@example.com",
    "password": "Secret123"
  }'
```

### 创建文章

```bash
curl -X POST http://127.0.0.1:8000/articles/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "我的第一篇文章",
    "content": "Hello FastAPI!",
    "author_id": 1
  }'
```

## Pydantic 校验示例

`schemas.py` 中体现以下校验：

- `username`：长度 3–20，仅字母数字下划线
- `email`：标准邮箱格式
- `password`：长度 6–32，必须包含字母与数字
- `title`：非空，长度 1–100
- `content`：非空

校验失败时，FastAPI 自动返回 HTTP 422 与详细错误信息。

## 技术要点

- **依赖注入**：`Depends(get_db)` 在每个请求中获取数据库 Session
- **Pydantic V2**：使用 `Field`、`EmailStr`、`field_validator` 进行校验
- **ORM 模型与 Schema 分离**：避免敏感字段（如 password）直接出现在响应中
- **APIRouter 模块化**：用户与文章路由分离，便于扩展
- **自动文档**：`tags`、`summary`、`response_model` 让 Swagger 文档更友好

## 扩展思路

- 增加用户登录与 JWT 鉴权
- 文章支持软删除（is_deleted 字段）
- 增加文章分类 / 标签
- 接入 MySQL / PostgreSQL
- 增加单元测试 (pytest + httpx)
