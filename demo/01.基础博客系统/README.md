# 01. 基础博客系统 (Django Demo)

一个使用 Django 实现的经典博客系统 Demo，包含用户认证、文章 CRUD、评论系统与 Admin 后台。

## 功能特性

| 模块 | 说明 |
| --- | --- |
| 用户注册登录 | 自定义注册视图 + Django 内置登录/登出 |
| 文章发布 / 编辑 / 删除 | 基于类视图 (CBV)，仅作者可编辑/删除 |
| 评论系统 | 登录用户可在文章详情页发表评论 |
| Django Admin 后台 | 文章、评论、用户的可视化管理 |
| 前端 UI | Bootstrap 5 CDN，简洁响应式布局 |

## 项目结构

```
01. 基础博客系统/
├── manage.py
├── db.sqlite3                # 运行 migrate 后生成
├── requirements.txt
├── blog_project/             # Django 项目配置
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/                 # 用户注册登录 App
│   ├── forms.py              # UserRegisterForm
│   ├── views.py              # register / login
│   ├── urls.py
│   └── admin.py
├── blog/                     # 文章 + 评论 App
│   ├── models.py             # Article, Comment
│   ├── forms.py              # ArticleForm, CommentForm
│   ├── views.py              # 列表/详情/CRV/评论
│   ├── urls.py
│   └── admin.py
├── templates/
│   ├── base.html
│   ├── registration/
│   │   ├── login.html
│   │   └── register.html
│   └── blog/
│       ├── article_list.html
│       ├── article_detail.html
│       ├── article_form.html
│       └── article_confirm_delete.html
└── static/
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
# 或者: pip install "Django>=5.0"
```

### 2. 进入项目目录

```bash
cd "demo/01. 基础博客系统"
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
| http://127.0.0.1:8000/ | 博客首页（自动跳转至 /blog/） |
| http://127.0.0.1:8000/blog/ | 文章列表 |
| http://127.0.0.1:8000/accounts/register/ | 用户注册 |
| http://127.0.0.1:8000/accounts/login/ | 用户登录 |
| http://127.0.0.1:8000/admin/ | Django Admin 后台 |

## URL 路由总览

| 命名 | URL | 说明 |
| --- | --- | --- |
| `home` | `/` | 重定向到博客首页 |
| `blog:article_list` | `/blog/` | 文章列表（分页） |
| `blog:article_detail` | `/blog/article/<pk>/` | 文章详情 |
| `blog:article_create` | `/blog/article/new/` | 发布文章（需登录） |
| `blog:article_edit` | `/blog/article/<pk>/edit/` | 编辑文章（仅作者） |
| `blog:article_delete` | `/blog/article/<pk>/delete/` | 删除文章（仅作者） |
| `blog:add_comment` | `/blog/article/<pk>/comment/` | 提交评论（需登录） |
| `accounts:register` | `/accounts/register/` | 注册 |
| `accounts:login` | `/accounts/login/` | 登录 |
| `accounts:logout` | `/accounts/logout/` | 登出 |
| admin | `/admin/` | 后台管理 |

## 权限说明

- **游客**：可浏览文章列表与详情，可阅读评论；不可发表评论、不可发布文章
- **登录用户**：可发布文章、编辑/删除自己的文章、对任意文章发表评论
- **超级用户**：拥有所有登录用户权限，并可在 Admin 后台管理所有文章、评论、用户

## 技术要点

- **基于类的视图 (CBV)**：使用 `ListView` / `DetailView` / `CreateView` / `UpdateView` / `DeleteView`
- **权限控制**：`LoginRequiredMixin` 限制登录访问，`UserPassesTestMixin` 限制仅作者可编辑/删除
- **表单校验**：自定义 `UserRegisterForm` 校验两次密码一致性
- **模板继承**：`base.html` 抽出公共导航与布局，子模板填充 `content` 块
- **中文本地化**：`LANGUAGE_CODE = 'zh-hans'`，`TIME_ZONE = 'Asia/Shanghai'`

## 扩展思路

- 增加 Markdown 支持 (`django-markdownx`)
- 增加文章标签、分类
- 增加文章点赞 / 收藏
- 增加 AJAX 异步评论
- 使用类视图 + slug 友好 URL
