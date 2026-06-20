# 03. 高性能博客API (FastAPI Demo)

基于 **FastAPI + 异步 SQLAlchemy (aiosqlite)** 实现的高性能博客 API Demo，包含 **用户 / 文章 / 标签 / 评论** 四大资源，支持异步查询、多对多标签、文章评论、API 分页与浏览量统计。

## 功能特性

| 模块 | 说明 |
| --- | --- |
| 异步数据库 | SQLAlchemy 2.0 `AsyncSession` + `aiosqlite`，全链路非阻塞 |
| 标签系统 | 文章 - 标签多对多关联，支持按标签筛选 |
| 评论系统 | 文章一对多评论，按时间排序 |
| API 分页 | `page` / `size` 参数，返回 total / pages 元数据 |
| 多条件筛选 | 按标签 / 作者 / 标题关键词筛选 |
| 浏览量统计 | `UPDATE ... SET view_count = view_count + 1`，避免读改写竞争 |
| 关系预加载 | `selectinload` 避免 N+1 查询问题 |

## 项目结构

```
03.高性能博客API/
├── main.py                # 应用入口（lifespan 建表）
├── config.py              # 配置（数据库 URL、分页参数）
├── database.py            # 异步引擎 / AsyncSession
├── models.py              # ORM 模型 (User / Tag / Post / Comment)
├── schemas.py             # Pydantic 模型 + 通用分页响应
├── deps.py                # 依赖项
├── crud/
│   ├── __init__.py
│   ├── user.py            # 用户 CRUD
│   ├── tag.py             # 标签 CRUD
│   ├── post.py            # 文章 CRUD + 分页 + 浏览量
│   └── comment.py         # 评论 CRUD
├── routers/
│   ├── __init__.py
│   ├── users.py           # 用户路由
│   ├── tags.py            # 标签路由
│   └── posts.py           # 文章路由 + 评论子资源
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
cd "demo/03.高性能博客API"
```

### 3. 启动开发服务器

```bash
uvicorn main:app --reload
```

首次启动时通过 `lifespan` 自动建表并生成 `blog_demo.db`。

### 4. 访问

| 地址 | 说明 |
| --- | --- |
| http://127.0.0.1:8000/ | 根路径欢迎页 |
| http://127.0.0.1:8000/docs | Swagger UI |
| http://127.0.0.1:8000/redoc | ReDoc 文档 |

## 接口一览

### 用户 `/users`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/users/` | 创建用户 |
| GET | `/users/` | 用户列表 |
| GET | `/users/{id}` | 用户详情 |

### 标签 `/tags`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/tags/` | 创建标签 |
| GET | `/tags/` | 标签列表 |
| DELETE | `/tags/{id}` | 删除标签 |

### 文章 `/posts`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/posts/` | 创建文章（可指定 tag_ids） |
| GET | `/posts/` | 文章列表（分页，支持 tag_id/author_id/keyword） |
| GET | `/posts/{id}` | 文章详情（浏览量 +1） |
| PUT | `/posts/{id}` | 更新文章 |
| DELETE | `/posts/{id}` | 删除文章 |
| POST | `/posts/{id}/comments` | 发表评论 |
| DELETE | `/posts/{id}/comments/{cid}` | 删除评论 |

## 使用示例

### 创建标签

```bash
curl -X POST http://127.0.0.1:8000/tags/ \
  -H "Content-Type: application/json" \
  -d '{"name": "FastAPI"}'
```

### 创建文章（关联标签）

```bash
curl -X POST http://127.0.0.1:8000/posts/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "FastAPI 异步指南",
    "content": "使用 async SQLAlchemy...",
    "author_id": 1,
    "tag_ids": [1]
  }'
```

### 分页查询文章

```bash
curl "http://127.0.0.1:8000/posts/?page=1&size=5&tag_id=1&keyword=FastAPI"
```

响应：

```json
{
  "items": [ ... ],
  "meta": {"page": 1, "size": 5, "total": 12, "pages": 3}
}
```

## 技术要点

- **异步 SQLAlchemy**：`create_async_engine` + `async_sessionmaker` + `AsyncSession`，所有查询 `await db.execute(select(...))`
- **aiosqlite 驱动**：连接串使用 `sqlite+aiosqlite:///...` 协议
- **selectinload 预加载**：避免加载关系时的 N+1 查询
- **浏览量原子自增**：`UPDATE ... SET view_count = view_count + 1`，避免读改写竞争
- **lifespan 事件**：启动建表，关闭释放连接池
- **通用分页响应**：`{items, meta:{page,size,total,pages}}` 统一结构

## 扩展思路

- 引入 Alembic 异步迁移
- 接入 PostgreSQL + asyncpg
- 文章全文搜索（如接入 whoosh / Elasticsearch）
- 评论支持嵌套回复（自引用外键）
- 增加缓存层（Redis 缓存热门文章）
