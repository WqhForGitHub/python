# 04. 开发模板项目 (Django Demo)

一个可复用的 Django 项目起始模板（Scaffold），内置自定义用户模型、基础页面、中间件、上下文处理器、模板标签、自定义管理命令等常用基础设施。开发者可直接复制本目录用于开启新项目。

## 功能特性

| 模块 | 说明 |
| --- | --- |
| 自定义用户模型 | `accounts.User` 继承 `AbstractUser`，扩展 `phone` / `avatar` 字段 |
| 用户认证 | 注册 / 登录 / 登出 / 个人资料，使用 CBV + `LoginRequiredMixin` |
| 公共基础设施 | `core` 应用提供抽象基类、中间件、上下文处理器、模板标签 |
| 请求耗时监控 | `RequestTimingMiddleware` 在响应头注入 `X-Request-Duration` |
| 自定义管理命令 | `wait_for_db` 等待数据库就绪，便于容器化部署 |
| 自定义错误页 | 404 / 500 页面与处理器 |
| 环境变量配置 | 通过 `os.environ` 读取敏感配置，`.env.example` 提供示例 |
| 前端 UI | Bootstrap 5 CDN，简洁响应式布局 |

## 项目结构

```
04.开发模板项目/
├── manage.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
├── template_project/          # Django 项目配置
│   ├── __init__.py
│   ├── settings.py            # 分离式配置：读取环境变量
│   ├── urls.py                # 根路由 + 404/500 处理器
│   ├── wsgi.py
│   └── asgi.py
├── core/                      # 公共基础设施 App
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py              # TimestampedModel 抽象基类
│   ├── admin.py
│   ├── views.py               # home / about / handler404 / handler500
│   ├── urls.py
│   ├── middleware.py          # RequestTimingMiddleware
│   ├── context_processors.py  # app_info
│   ├── templatetags/
│   │   ├── __init__.py
│   │   └── core_tags.py       # {% current_year %}
│   ├── management/
│   │   ├── __init__.py
│   │   └── commands/
│   │       ├── __init__.py
│   │       └── wait_for_db.py
│   └── migrations/
│       └── __init__.py
├── accounts/                  # 用户认证 App
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py              # User(AbstractUser)
│   ├── admin.py               # 自定义 UserAdmin
│   ├── forms.py               # 注册 / 登录 / 资料表单
│   ├── views.py               # register / login / logout / profile
│   ├── urls.py
│   └── migrations/
│       ├── __init__.py
│       └── 0001_initial.py    # 自定义 User 初始迁移
├── templates/
│   ├── base.html
│   ├── 404.html
│   ├── 500.html
│   ├── core/
│   │   ├── home.html
│   │   └── about.html
│   ├── registration/
│   │   ├── login.html
│   │   └── register.html
│   └── accounts/
│       └── profile.html
└── static/
    ├── css/
    │   └── style.css
    ├── js/
    │   └── main.js
    └── img/
        └── .gitkeep
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
# 或者: pip install "Django>=5.0"
```

### 2. 进入项目目录

```bash
cd "demo/04.开发模板项目"
```

### 3. 复制环境变量示例文件（可选）

```bash
cp .env.example .env
# 按需修改 .env 中的配置项
```

### 4. 生成数据库迁移并执行

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. 创建超级用户（用于访问 Admin 后台）

```bash
python manage.py createsuperuser
```

### 6. 启动开发服务器

```bash
python manage.py runserver
```

### 7. 访问

| 地址 | 说明 |
| --- | --- |
| http://127.0.0.1:8000/ | 首页 |
| http://127.0.0.1:8000/about/ | 关于页面 |
| http://127.0.0.1:8000/accounts/register/ | 用户注册 |
| http://127.0.0.1:8000/accounts/login/ | 用户登录 |
| http://127.0.0.1:8000/accounts/profile/ | 个人资料（需登录） |
| http://127.0.0.1:8000/admin/ | Django Admin 后台 |

## URL 路由总览

| 命名 | URL | 说明 |
| --- | --- | --- |
| `core:home` | `/` | 首页 |
| `core:about` | `/about/` | 关于页面 |
| `accounts:register` | `/accounts/register/` | 用户注册 |
| `accounts:login` | `/accounts/login/` | 用户登录 |
| `accounts:logout` | `/accounts/logout/` | 用户登出 |
| `accounts:profile` | `/accounts/profile/` | 个人资料（需登录） |
| admin | `/admin/` | 后台管理 |

## 技术要点

- **自定义用户模型**：在项目初期通过 `AUTH_USER_MODEL = 'accounts.User'` 替换默认 User，避免后期迁移痛点
- **基于类的视图 (CBV)**：`CreateView` / `LoginView` / `LogoutView` / `UpdateView` + `LoginRequiredMixin`
- **中间件**：自定义 `RequestTimingMiddleware` 演示请求耗时统计
- **上下文处理器**：`app_info` 向所有模板注入站点名称与版本号
- **自定义模板标签**：`{% current_year %}` 演示简单标签库写法
- **抽象基类**：`TimestampedModel` 提供 `created_at` / `updated_at` 公共字段
- **环境变量配置**：`SECRET_KEY` / `DEBUG` / `ALLOWED_HOSTS` 从 `os.environ` 读取，便于多环境部署
- **自定义管理命令**：`wait_for_db` 适配容器化场景下的数据库就绪等待
- **中文本地化**：`LANGUAGE_CODE = 'zh-hans'`，`TIME_ZONE = 'Asia/Shanghai'`

## 扩展思路

- 引入 `django-environ` 或 `python-dotenv` 统一管理 `.env`
- 拆分 `settings.py` 为 `base.py` / `dev.py` / `prod.py` 多环境配置
- 接入 `django-debug-toolbar` 辅助调试
- 使用 `django-crispy-forms` 美化表单渲染
- 增加 Docker / docker-compose 部署模板
- 增加基于角色的权限控制 (RBAC)
- 增加 API 模块（如需可引入 Django Ninja 或 DRF）
