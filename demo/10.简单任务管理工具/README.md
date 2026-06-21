# 10. 简单任务管理工具 (Django Demo)

一个使用 Django 实现的看板式任务管理工具 Demo，类似 Trello 简化版，支持看板、列表（列）、卡片的三级结构，包含优先级、标签、负责人、截止日期与卡片移动功能。

## 功能特性

| 模块 | 说明 |
| --- | --- |
| 用户注册登录 | 自定义 User 模型（头像 + 简介），注册 / 登录 / 登出 / 个人资料 |
| 看板管理 | 创建 / 编辑 / 删除看板，支持多人协作（成员） |
| 列表（列）管理 | 在看板中添加列表，可排序 |
| 卡片管理 | 创建 / 编辑 / 删除卡片，支持标题、描述、负责人、优先级、标签、截止日期 |
| 卡片移动 | 通过表单将卡片在列之间移动并排序（无需 JS 拖拽） |
| 权限控制 | 看板仅所有者与成员可访问；删除仅限所有者；卡片编辑限所有者或负责人 |
| Django Admin 后台 | 看板、列、卡片、用户的可视化管理 |
| 前端 UI | Bootstrap 5 CDN，横向滚动的看板布局，颜色化优先级徽章 |

## 项目结构

```
10. 简单任务管理工具/
├── manage.py
├── requirements.txt
├── README.md
├── task_project/            # Django 项目配置
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/                # 用户注册登录 App
│   ├── models.py            # 自定义 User (AbstractUser)
│   ├── forms.py             # UserRegisterForm, ProfileForm
│   ├── views.py             # register, profile
│   ├── urls.py
│   ├── admin.py
│   └── migrations/
├── boards/                  # 看板 + 列 + 卡片 App
│   ├── models.py            # Board, Column, Card
│   ├── forms.py             # BoardForm, ColumnForm, CardForm, CardMoveForm
│   ├── views.py             # 列表/详情/CRUD/卡片移动
│   ├── urls.py
│   ├── admin.py
│   └── migrations/
├── templates/
│   ├── base.html
│   ├── registration/
│   │   ├── login.html
│   │   └── register.html
│   ├── accounts/
│   │   └── profile.html
│   └── boards/
│       ├── board_list.html
│       ├── board_detail.html
│       ├── board_form.html
│       ├── board_confirm_delete.html
│       └── includes/
│           ├── card_form.html
│           └── card_move_form.html
└── static/
    ├── css/style.css
    ├── js/main.js
    └── img/
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
# 或者: pip install "Django>=5.0"
```

### 2. 进入项目目录

```bash
cd "demo/10. 简单任务管理工具"
```

### 3. 生成数据库迁移并执行

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. 创建超级用户（用于访问 Admin 后台）

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
| http://127.0.0.1:8000/ | 看板列表（未登录跳转登录） |
| http://127.0.0.1:8000/accounts/register/ | 用户注册 |
| http://127.0.0.1:8000/accounts/login/ | 用户登录 |
| http://127.0.0.1:8000/accounts/profile/ | 个人资料 |
| http://127.0.0.1:8000/boards/new/ | 新建看板 |
| http://127.0.0.1:8000/admin/ | Django Admin 后台 |

## URL 路由总览

| 命名 | URL | 说明 |
| --- | --- | --- |
| `boards:board_list` | `/` | 看板列表（需登录） |
| `boards:board_create` | `/boards/new/` | 新建看板 |
| `boards:board_detail` | `/boards/<pk>/` | 看板详情（看板视图） |
| `boards:board_edit` | `/boards/<pk>/edit/` | 编辑看板 |
| `boards:board_delete` | `/boards/<pk>/delete/` | 删除看板（仅所有者） |
| `boards:column_create` | `/boards/<pk>/columns/new/` | 添加列表 |
| `boards:card_create` | `/columns/<pk>/cards/new/` | 添加卡片 |
| `boards:card_edit` | `/cards/<pk>/edit/` | 编辑卡片 |
| `boards:card_delete` | `/cards/<pk>/delete/` | 删除卡片 |
| `boards:card_move` | `/cards/<pk>/move/` | 移动卡片 |
| `accounts:register` | `/accounts/register/` | 注册 |
| `accounts:login` | `/accounts/login/` | 登录 |
| `accounts:logout` | `/accounts/logout/` | 登出 |
| `accounts:profile` | `/accounts/profile/` | 个人资料 |
| admin | `/admin/` | 后台管理 |

## 数据模型

- **Board（看板）**：标题、描述、所有者（owner）、成员（members）、归档状态
- **Column（列）**：所属看板、标题、排序
- **Card（卡片）**：所属列、标题、描述、负责人、标签、优先级（low/medium/high/urgent）、截止日期、排序

## 权限说明

- **游客**：仅可访问注册 / 登录页
- **登录用户**：可创建看板、访问自己拥有或被加入为成员的看板、在看板中添加列与卡片、编辑自己负责的卡片
- **看板所有者**：拥有看板全部权限，可编辑 / 删除看板、管理成员
- **超级用户**：拥有所有权限，并可在 Admin 后台管理全部数据

## 技术要点

- **基于类的视图 (CBV)**：`ListView` / `DetailView` / `CreateView` / `UpdateView` / `DeleteView`
- **权限控制**：`LoginRequiredMixin` + `UserPassesTestMixin`，封装 `BoardAccessMixin`
- **自定义用户模型**：继承 `AbstractUser`，新增头像与简介字段
- **表单提交**：卡片移动通过原生 HTML 表单 POST 实现，无需 JavaScript 拖拽
- **模板继承**：`base.html` 抽出公共导航与布局，子模板填充 `content` 块
- **中文本地化**：`LANGUAGE_CODE = 'zh-hans'`，`TIME_ZONE = 'Asia/Shanghai'`

## 扩展思路

- 增加 JavaScript 拖拽排序（HTML5 Drag & Drop 或 SortableJS）
- 增加看板成员邀请与权限分级
- 增加卡片评论与附件
- 增加卡片活动日志
- 增加 REST API（Django REST Framework）
- 增加快捷键与搜索功能
