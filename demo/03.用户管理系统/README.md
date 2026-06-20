# 03. 用户管理系统 (Django Demo)

一个使用 **纯 Django** 实现的用户管理系统 Demo，涵盖自定义用户模型、注册登录、个人资料管理、用户增删改查与统计仪表盘。

## 功能特性

| 模块 | 说明 |
| --- | --- |
| 自定义用户模型 | 继承 `AbstractUser`，扩展邮箱/手机号/头像/简介/出生日期等字段 |
| 注册 / 登录 / 登出 | 自定义表单 + Bootstrap UI，注册后自动登录 |
| 个人资料 | 登录用户可查看、编辑自己的资料与头像 |
| 修改密码 | 基于内置 `PasswordChangeView`，带旧密码校验 |
| 用户列表 | 员工可见，支持按用户名/邮箱/手机号搜索 + 分页 |
| 用户增删改查 | 员工可新建、查看、编辑、删除用户（不可删除自己） |
| 仪表盘 | 员工可见，展示用户总数、启用/禁用、员工、近 7/30 天新增等统计 |
| Django Admin 后台 | 自定义 `UserAdmin`，支持扩展字段管理 |
| 前端 UI | Bootstrap 5 + Bootstrap Icons，响应式布局 |

## 项目结构

```
03. 用户管理系统/
├── manage.py
├── requirements.txt
├── db.sqlite3                # 运行 migrate 后生成
├── usermanage_project/       # Django 项目配置
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── users/                    # 用户管理 App
│   ├── models.py             # 自定义 User 模型
│   ├── forms.py              # 注册/登录/资料/管理员/改密 表单
│   ├── views.py              # CBV: 仪表盘/列表/详情/CRUD/资料/改密
│   ├── urls.py
│   └── admin.py
├── templates/
│   ├── base.html
│   ├── registration/
│   │   ├── login.html
│   │   └── register.html
│   └── users/
│       ├── dashboard.html
│       ├── user_list.html
│       ├── user_detail.html
│       ├── user_form.html
│       ├── user_confirm_delete.html
│       ├── profile.html
│       ├── profile_edit.html
│       └── password_change.html
├── static/
│   └── css/style.css
└── media/                    # 用户头像上传目录（运行后自动生成）
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
# 或者: pip install "Django>=5.0"
```

### 2. 进入项目目录

```bash
cd "demo/03. 用户管理系统"
```

### 3. 生成数据库迁移并执行

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. 创建超级用户（用于访问 Admin 后台与员工功能）

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
| http://127.0.0.1:8000/ | 仪表盘（自动跳转至 /users/，需员工登录） |
| http://127.0.0.1:8000/users/login/ | 登录 |
| http://127.0.0.1:8000/users/register/ | 注册 |
| http://127.0.0.1:8000/users/list/ | 用户列表（员工可见） |
| http://127.0.0.1:8000/users/profile/ | 个人资料（登录可见） |
| http://127.0.0.1:8000/admin/ | Django Admin 后台 |

## URL 路由总览

| 命名 | URL | 说明 |
| --- | --- | --- |
| `home` | `/` | 重定向到仪表盘 |
| `users:login` | `/users/login/` | 登录 |
| `users:register` | `/users/register/` | 注册 |
| `users:logout` | `/users/logout/` | 登出 |
| `users:dashboard` | `/users/` | 仪表盘（员工） |
| `users:user_list` | `/users/list/` | 用户列表（员工，支持 ?q= 搜索 & ?page= 分页） |
| `users:user_create` | `/users/create/` | 新建用户（员工） |
| `users:user_detail` | `/users/<pk>/` | 用户详情（员工） |
| `users:user_edit` | `/users/<pk>/edit/` | 编辑用户（员工） |
| `users:user_delete` | `/users/<pk>/delete/` | 删除用户（员工，不可删除自己） |
| `users:profile` | `/users/profile/` | 个人资料（登录） |
| `users:profile_edit` | `/users/profile/edit/` | 编辑个人资料（登录） |
| `users:password_change` | `/users/password/change/` | 修改密码（登录） |
| admin | `/admin/` | 后台管理 |

## 权限说明

- **游客**：仅可访问注册与登录页面
- **登录用户（普通）**：可查看与编辑自己的个人资料、修改密码
- **登录用户（员工 is_staff）**：在普通用户基础上，可访问仪表盘、用户列表，并对用户进行增删改查
- **超级用户（is_superuser）**：拥有所有员工权限，并可在 Admin 后台管理一切

> 说明：注册的新用户默认为普通用户。如需让某用户具备管理权限，可由超级管理员在 Admin 后台或员工管理页面勾选「是否员工」。

## 技术要点

- **自定义用户模型**：`AUTH_USER_MODEL = 'users.User'`，从头开始自定义以避免后期迁移难题（最佳实践）
- **基于类的视图 (CBV)**：`ListView` / `DetailView` / `CreateView` / `UpdateView` / `DeleteView` / `TemplateView`
- **权限控制**：`LoginRequiredMixin` 限制登录访问；自定义 `StaffRequiredMixin`（继承 `UserPassesTestMixin`）限制员工访问
- **表单校验**：注册时校验两次密码一致性、邮箱唯一性；管理员编辑时密码可选（留空保持不变）
- **搜索与分页**：用户列表支持 `Q` 对象多字段模糊搜索与 `paginate_by` 分页
- **媒体文件**：头像上传至 `MEDIA_ROOT`，开发环境通过 `static()` 服务
- **模板继承**：`base.html` 抽出导航与布局，子模板填充 `content` 块
- **消息框架**：操作成功/失败通过 `django.contrib.messages` 反馈

## 扩展思路

- 增加用户角色（Role）与细粒度权限分组（Group）
- 增加用户登录日志、操作审计
- 增加导出用户为 Excel / CSV
- 增加头像裁剪上传 (`django-cropper-image`)
- 增加 REST API（结合 DRF）
- 增加邮箱验证注册流程
