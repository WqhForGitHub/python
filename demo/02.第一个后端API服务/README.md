# 02. 第一个后端API服务 (Django Demo)

一个使用 **纯 Django**（不依赖 Django REST Framework）实现的后端 API 服务 Demo，以 Task（任务）资源为例演示完整的 RESTful CRUD 接口。

## 功能特性

| 模块 | 说明 |
| --- | --- |
| RESTful CRUD | 对 Task 资源实现 GET / POST / PUT / PATCH / DELETE 全套接口 |
| JSON 请求与响应 | 手动解析 JSON 请求体、手动序列化模型为 JSON 字典 |
| 数据校验 | 手动编写字段级校验逻辑（必填、长度、类型），返回结构化错误信息 |
| 分页 | `?page=&page_size=` 查询参数分页，返回 count / total_pages 等元信息 |
| 过滤与搜索 | `?completed=true/false` 按状态过滤，`?search=关键字` 按标题模糊搜索 |
| 排序 | `?sort=-created_at` 按白名单字段排序，防止 SQL 注入 |
| HTTP 状态码 | 正确使用 200 / 201 / 400 / 404 / 405 等状态码 |
| JSON 错误处理 | 自定义全局 404 / 500 处理器，统一返回 JSON |
| Django Admin | 提供可视化的任务管理后台，支持搜索 / 过滤 / 批量编辑 |

## 项目结构

```
02.第一个后端API服务/
├── manage.py
├── db.sqlite3                # 运行 migrate 后生成
├── requirements.txt
├── api_project/              # Django 项目配置
│   ├── __init__.py
│   ├── settings.py           # 项目配置（含分页默认值）
│   ├── urls.py               # 根路由 + 自定义 JSON 错误处理器
│   ├── views.py              # API 根路径 / 健康检查 / 404 / 500 处理器
│   ├── wsgi.py
│   └── asgi.py
└── tasks/                    # 任务 App
    ├── __init__.py
    ├── apps.py
    ├── models.py             # Task 模型
    ├── serializers.py        # task_to_dict 序列化函数
    ├── views.py              # CRUD API 视图 + JSON 解析 / 校验工具
    ├── urls.py               # 任务路由
    ├── admin.py              # Admin 后台注册
    └── migrations/
        └── 0001_initial.py   # 初始迁移
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
# 或者: pip install "Django>=5.0"
```

### 2. 进入项目目录

```bash
cd "demo/02.第一个后端API服务"
```

### 3. 执行数据库迁移

```bash
python manage.py migrate
```

### 4. 创建超级用户（用于访问 Admin 后台，可选）

```bash
python manage.py createsuperuser
```

### 5. 启动开发服务器

```bash
python manage.py runserver
```

### 6. 访问

| 地址 | 说明 |
| --- | --- |
| http://127.0.0.1:8000/api/ | API 根路径（返回接口信息） |
| http://127.0.0.1:8000/api/health/ | 健康检查 |
| http://127.0.0.1:8000/api/tasks/ | 任务列表 / 创建 |
| http://127.0.0.1:8000/api/tasks/1/ | 单个任务详情 / 更新 / 删除 |
| http://127.0.0.1:8000/admin/ | Django Admin 后台 |

## 接口一览

### 任务列表与创建

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/tasks/` | 获取任务列表（支持分页、过滤、搜索、排序） |
| `POST` | `/api/tasks/` | 创建任务 |

### 任务详情与更新

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/tasks/<id>/` | 获取单个任务 |
| `PUT` | `/api/tasks/<id>/` | 全量更新任务（需提交所有字段） |
| `PATCH` | `/api/tasks/<id>/` | 部分更新任务（仅提交需要修改的字段） |
| `DELETE` | `/api/tasks/<id>/` | 删除任务 |

### 查询参数（GET /api/tasks/）

| 参数 | 说明 | 示例 |
| --- | --- | --- |
| `page` | 页码（从 1 开始） | `?page=2` |
| `page_size` | 每页条数（最大 100） | `?page_size=20` |
| `completed` | 按完成状态过滤 | `?completed=true` |
| `search` | 按标题模糊搜索 | `?search=Django` |
| `sort` | 排序字段（支持前缀 `-` 降序） | `?sort=-updated_at` |

### 其他端点

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/` | API 信息（返回可用端点列表） |
| `GET` | `/api/health/` | 健康检查 |

## 示例请求

### 创建任务

```bash
curl -X POST http://127.0.0.1:8000/api/tasks/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "学习 Django",
    "description": "完成第一个后端 API 服务 Demo",
    "completed": false
  }'
```

响应（201 Created）：

```json
{
  "id": 1,
  "title": "学习 Django",
  "description": "完成第一个后端 API 服务 Demo",
  "completed": false,
  "created_at": "2025-06-20T10:00:00+08:00",
  "updated_at": "2025-06-20T10:00:00+08:00"
}
```

### 获取任务列表

```bash
curl http://127.0.0.1:8000/api/tasks/
```

响应：

```json
{
  "count": 1,
  "page": 1,
  "page_size": 10,
  "total_pages": 1,
  "results": [ ... ]
}
```

### 过滤 + 搜索 + 分页

```bash
curl "http://127.0.0.1:8000/api/tasks/?completed=false&search=Django&page=1&page_size=5"
```

### 部分更新（PATCH）

```bash
curl -X PATCH http://127.0.0.1:8000/api/tasks/1/ \
  -H "Content-Type: application/json" \
  -d '{"completed": true}'
```

### 删除任务

```bash
curl -X DELETE http://127.0.0.1:8000/api/tasks/1/
```

响应（200 OK）：

```json
{
  "message": "任务已删除 (id=1)"
}
```

### 校验失败示例

```bash
curl -X POST http://127.0.0.1:8000/api/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"completed": "yes"}'
```

响应（400 Bad Request）：

```json
{
  "error": "数据校验失败",
  "errors": {
    "title": "该字段为必填项",
    "completed": "该字段必须为布尔值"
  }
}
```

## 数据模型

### Task（任务）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BigAutoField | 主键，自增 |
| `title` | CharField(200) | 标题（必填） |
| `description` | TextField | 描述（可选，默认空字符串） |
| `completed` | BooleanField | 是否完成（默认 false） |
| `created_at` | DateTimeField | 创建时间（自动生成） |
| `updated_at` | DateTimeField | 更新时间（自动更新） |

## 技术要点

- **纯 Django 无 DRF**：使用 `JsonResponse` 返回 JSON，`json.loads` 解析请求体，手动编写序列化与校验逻辑，帮助理解 API 底层原理
- **RESTful 设计**：遵循 REST 规范，使用正确的 HTTP 方法与状态码（200 / 201 / 400 / 404 / 405）
- **函数视图 + 方法分发**：每个视图函数内通过 `request.method` 分发到对应的处理逻辑，清晰直观
- **手动数据校验**：`validate_task_data()` 实现 PUT 全量校验与 PATCH 部分校验，返回字段级错误信息
- **Django Paginator 分页**：使用内置分页器，配合查询参数 `page` / `page_size` 实现灵活分页
- **排序白名单**：通过 `SORT_FIELDS` 集合限制可排序字段，防止恶意排序导致的 SQL 注入
- **CSRF 豁免**：API 视图使用 `@csrf_exempt` 装饰器，便于命令行 / 前端跨域调用；生产环境应替换为 Token / JWT 认证
- **自定义 JSON 错误处理器**：通过 `handler404` / `handler500` 配置全局错误返回 JSON（DEBUG=False 时生效）
- **中文本地化**：`LANGUAGE_CODE = 'zh-hans'`，`TIME_ZONE = 'Asia/Shanghai'`

## 扩展思路

- 引入 Token / JWT 认证，替换 `@csrf_exempt`
- 使用 Django REST Framework 重构，对比纯手写的差异
- 增加用户模型与任务关联（`owner` 外键），实现按用户过滤
- 增加任务标签 / 分类（多对多关系）
- 增加接口限流（`django-ratelimit`）
- 编写 `pytest` + `django-pytest` 接口测试
- 部署到生产环境：Gunicorn + Nginx + PostgreSQL
