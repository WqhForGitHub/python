# 在线课程管理平台 - Django Demo

一个基于纯 Django 5.x 的在线课程管理平台示例项目，支持课程管理、课时管理、分类管理、学员选课，以及教师/学员角色区分。

## 功能特性

- **用户系统**：自定义 User 模型，支持 `student`（学员）、`teacher`（教师）、`admin`（管理员）三种角色
- **课程管理**：教师可创建、编辑课程；课程包含标题、描述、分类、封面、价格、发布状态
- **课时管理**：教师可为课程添加课时，包含文本内容与视频链接
- **分类管理**：课程按分类组织，前台支持分类筛选
- **选课功能**：学员可 enroll 课程，并查看已选课程
- **权限控制**：教师才能创建/编辑课程与课时；学员需选课后才能查看课时详情
- **前台界面**：基于 Bootstrap 5 的简洁中文界面

## 技术栈

- Python >= 3.10
- Django >= 5.0（纯 Django，不使用 DRF）
- SQLite 数据库
- Bootstrap 5（CDN）

## 目录结构

```
07.在线课程管理平台/
├── manage.py                 # Django 管理脚本
├── requirements.txt          # 依赖声明（PEP 621）
├── README.md
├── .gitignore
├── course_project/           # 项目配置包
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/                 # 用户应用
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py             # 自定义 User 模型
│   ├── admin.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   └── migrations/
├── courses/                  # 课程应用
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py             # Category / Course / Lesson / Enrollment
│   ├── admin.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   └── migrations/
├── templates/                # 模板
│   ├── base.html
│   ├── courses/
│   ├── registration/
│   └── accounts/
└── static/                   # 静态资源
    ├── css/
    └── img/
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 执行数据库迁移

```bash
python manage.py migrate
```

### 3. 创建超级用户

```bash
python manage.py createsuperuser
```

### 4. 启动开发服务器

```bash
python manage.py runserver
```

访问 http://127.0.0.1:8000/ 进入平台首页。

## 使用说明

1. **注册账号**：访问 `/accounts/register/` 注册新账号，可选择学员或教师角色。
2. **创建课程**：以教师身份登录后，点击「创建课程」。
3. **添加课时**：在课程详情页，教师可点击「添加课时」。
4. **选课学习**：以学员身份登录，在课程详情页点击「选课」，之后即可查看课时内容。
5. **我的课程**：访问 `/courses/my/` 查看已选课程（学员）或所授课程（教师）。
6. **后台管理**：访问 `/admin/`（需超级用户），可管理分类、课程、课时、选课记录。

## 配置说明

- `LANGUAGE_CODE = 'zh-hans'`
- `TIME_ZONE = 'Asia/Shanghai'`
- `USE_TZ = True`
- `AUTH_USER_MODEL = 'accounts.User'`
- 登录后跳转至课程列表页

## 演示账号建议

- 学员：用户名 `student1`，角色 `student`
- 教师：用户名 `teacher1`，角色 `teacher`
- 管理员：通过 `createsuperuser` 创建

> 本项目仅用于学习演示，请勿用于生产环境。
