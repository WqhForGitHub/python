# 企业后台管理系统 (Enterprise Backend Management System)

> 一个基于 Django 5.x 的企业内部后台管理系统演示项目，包含部门、员工、项目、任务的完整管理功能，具备角色访问控制与数据统计仪表盘。

## 项目简介

本项目是一个纯 Django 实现的企业后台管理系统，强调 Django Admin 自定义配置与自定义仪表盘展示。系统支持三种角色（普通员工、部门经理、管理员），并提供了基于角色的访问控制（RBAC）。

### 主要功能

- **仪表盘 (Dashboard)**：统计员工总数、部门数、项目状态分布、任务状态分布、部门人员分布、最近项目与员工列表。
- **部门管理 (Departments)**：部门的增删改查、层级部门（父部门）支持。
- **员工管理 (Employees)**：员工的增删改查、按部门/状态/关键字搜索过滤。
- **项目管理 (Projects)**：项目的增删改查、项目成员、项目状态流转、预算与周期管理。
- **任务管理 (Tasks)**：任务的增删改查、任务状态快速切换、优先级管理。
- **账户管理 (Accounts)**：自定义用户模型、登录/登出、个人资料编辑。
- **Django Admin 自定义**：用户、部门、员工、项目、任务的 Admin 配置与内联展示。

### 角色说明

| 角色 | 标识 | 权限 |
| --- | --- | --- |
| 普通员工 | `staff` | 查看所有数据 |
| 部门经理 | `manager` | 查看数据 + 增删改部门/员工/项目/任务 |
| 管理员 | `admin` | 全部权限 |
| 超级用户 | `is_superuser` | 全部权限（含 Admin 后台） |

## 技术栈

- Python >= 3.10
- Django >= 5.0
- SQLite（默认数据库）
- Bootstrap 5（CDN）
- Pillow（头像图片处理）

## 目录结构

```
09.企业后台管理系统/
├── manage.py                # 管理脚本
├── requirements.txt         # 依赖（PEP 621 格式）
├── README.md                # 项目说明
├── .gitignore
├── admin_project/           # Django 项目配置
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/                # 账户应用（自定义用户）
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py
│   ├── admin.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   └── migrations/
│       ├── __init__.py
│       ├── 0001_initial.py
│       └── 0002_user_department.py
├── employees/               # 员工与部门应用
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
├── projects/                # 项目与任务应用
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
├── dashboard/               # 仪表盘应用
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── migrations/
│       └── __init__.py
├── templates/               # 模板目录
│   ├── base.html
│   ├── dashboard/
│   ├── employees/
│   ├── projects/
│   └── accounts/
└── static/                  # 静态资源
    ├── css/style.css
    ├── js/main.js
    └── img/.gitkeep
```

## 快速开始

### 1. 安装依赖

```bash
cd "09.企业后台管理系统"
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 2. 执行数据库迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

> 注意：本项目已内置初始迁移文件，可直接执行 `python manage.py migrate`。

### 3. 创建超级管理员

```bash
python manage.py createsuperuser
```

### 4. 启动开发服务器

```bash
python manage.py runserver
```

### 5. 访问系统

- 自定义仪表盘：http://127.0.0.1:8000/
- Django Admin 后台：http://127.0.0.1:8000/admin/
- 登录页面：http://127.0.0.1:8000/accounts/login/

## 使用说明

1. 首次访问会自动跳转到登录页面。
2. 使用 `createsuperuser` 创建的账号登录后，可在「Admin 后台」中录入部门、员工、项目、任务等基础数据。
3. 在自定义仪表盘查看统计信息。
4. 部门经理（`manager`）与管理员（`admin`）角色可在自定义页面进行增删改操作。
5. 普通员工（`staff`）仅可查看数据。

## 演示数据建议

可通过 Django Admin 录入如下示例数据：

- 部门：研发部、产品部、市场部、人力资源部、财务部
- 员工：若干（绑定用户与部门）
- 项目：3-5 个不同状态的项目
- 任务：每个项目若干任务

## 许可证

本项目仅用于学习演示，无商业许可。
