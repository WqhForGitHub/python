# 博客评论互动系统 - Django Demo

一个基于纯 Django 5.x 的博客评论互动系统示例，包含文章发布、嵌套评论、点赞、标签等功能。

## 功能特性

- **用户系统**：自定义用户模型，支持昵称、头像、个人简介，注册与资料编辑
- **文章管理**：发表、编辑、删除文章，支持封面图、摘要、标签
- **标签系统**：文章多标签分类，标签云展示，按标签筛选文章
- **嵌套评论**：支持多级回复，递归渲染评论树
- **点赞功能**：登录用户可对文章点赞/取消点赞
- **搜索功能**：按标题或内容搜索文章
- **浏览量统计**：访问文章详情自动累加浏览量
- **分页**：文章列表分页展示（每页 10 篇）

## 技术栈

- Python >= 3.10
- Django >= 5.0（纯 Django，不使用 DRF）
- SQLite 数据库
- Bootstrap 5（CDN）
- Pillow（图像处理）

## 目录结构

```
08.博客评论互动系统/
├── manage.py                 # Django 管理脚本
├── requirements.txt          # 项目依赖
├── README.md                 # 项目说明
├── .gitignore
├── blog_project/             # 项目配置包
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/                 # 用户应用
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py
│   ├── admin.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   └── migrations/
│       ├── __init__.py
│       └── 0001_initial.py
├── blog/                     # 博客应用
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py
│   ├── admin.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   └── migrations/
│       ├── __init__.py
│       └── 0001_initial.py
├── templates/                # 模板
│   ├── base.html
│   ├── blog/
│   │   ├── post_list.html
│   │   ├── post_detail.html
│   │   ├── post_form.html
│   │   ├── post_confirm_delete.html
│   │   └── includes/
│   │       ├── comment_tree.html
│   │       └── pagination.html
│   ├── registration/
│   │   ├── login.html
│   │   └── register.html
│   └── accounts/
│       └── profile.html
└── static/                   # 静态文件
    ├── css/
    │   └── style.css
    └── img/
        └── .gitkeep
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 执行数据库迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. 创建超级管理员

```bash
python manage.py createsuperuser
```

### 4. 启动开发服务器

```bash
python manage.py runserver
```

### 5. 访问站点

- 首页：http://127.0.0.1:8000/
- 后台管理：http://127.0.0.1:8000/admin/
- 登录：http://127.0.0.1:8000/accounts/login/
- 注册：http://127.0.0.1:8000/accounts/register/

## 配置说明

- 数据库：默认使用 SQLite（`db.sqlite3`，运行迁移后自动创建）
- 语言：简体中文（`zh-hans`）
- 时区：亚洲/上海（`Asia/Shanghai`）
- 媒体文件：上传的图片保存在 `media/` 目录（头像 `avatars/`，文章封面 `post_covers/`）
- 静态文件：`static/` 目录

## 主要 URL 路由

| 路径 | 名称 | 说明 |
|------|------|------|
| `/` | `blog:post_list` | 文章列表 |
| `/post/new/` | `blog:post_create` | 发表文章 |
| `/post/<slug>/` | `blog:post_detail` | 文章详情 |
| `/post/<slug>/edit/` | `blog:post_edit` | 编辑文章 |
| `/post/<slug>/delete/` | `blog:post_delete` | 删除文章 |
| `/post/<slug>/comment/` | `blog:comment_create` | 发表评论 |
| `/post/<slug>/like/` | `blog:like_toggle` | 点赞切换 |
| `/tag/<slug>/` | `blog:posts_by_tag` | 按标签筛选 |
| `/accounts/login/` | `accounts:login` | 登录 |
| `/accounts/register/` | `accounts:register` | 注册 |
| `/accounts/profile/` | `accounts:profile` | 个人资料 |

## 演示数据

可在 Django Admin 后台中手动添加标签、文章；或在登录后通过前台发表文章。

## 备注

本系统为教学演示用途，生产环境部署前请修改 `SECRET_KEY`、关闭 `DEBUG`、配置静态与媒体文件服务等。
