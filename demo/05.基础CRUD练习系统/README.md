# 05. 基础CRUD练习系统 (Django Demo)

一个使用 Django 实现的 **学生成绩管理** 系统 Demo，专注于练习 Create / Read / Update / Delete 四大基础操作。包含学生信息的增删改查、学生成绩录入、统计仪表盘与 Admin 后台。

## 功能特性

| 模块 | 说明 |
| --- | --- |
| 学生列表 / 详情 / 新建 / 编辑 / 删除 | 完整 CRUD，基于类视图 (CBV) 实现 |
| 学生搜索与筛选 | 按姓名 / 学号模糊搜索，按性别筛选 |
| 成绩管理 | 为学生添加多条成绩记录，可删除 |
| 统计仪表盘 | 总学生数、平均分、科目数、最近添加的学生 |
| 分页 | 列表页每页 10 条记录 |
| 登录认证 | 新建 / 编辑 / 删除操作需登录 (LoginRequiredMixin) |
| Django Admin 后台 | 学生与成绩的可视化管理 |
| 前端 UI | Bootstrap 5 CDN，简洁响应式布局 |

## 项目结构

```
05. 基础CRUD练习系统/
├── manage.py
├── db.sqlite3                      # 运行 migrate 后生成
├── requirements.txt
├── README.md
├── crud_project/                   # Django 项目配置
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── students/                       # 学生 + 成绩 App
│   ├── __init__.py
│   ├── apps.py                     # StudentsConfig
│   ├── models.py                   # Student, Grade
│   ├── forms.py                    # StudentForm, GradeForm, StudentSearchForm
│   ├── views.py                    # CBV: 列表/详情/CRUD + 仪表盘 + 成绩删除
│   ├── urls.py                     # 命名空间 'students'
│   ├── admin.py
│   └── migrations/
│       ├── __init__.py
│       └── 0001_initial.py         # 初始迁移
├── templates/
│   ├── base.html
│   ├── registration/
│   │   └── login.html
│   └── students/
│       ├── dashboard.html
│       ├── student_list.html
│       ├── student_detail.html
│       ├── student_form.html
│       └── student_confirm_delete.html
└── static/
    └── css/
        └── style.css
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
# 或者: pip install "Django>=5.0"
```

### 2. 进入项目目录

```bash
cd "demo/05.基础CRUD练习系统"
```

### 3. 执行数据库迁移

```bash
python manage.py migrate
```

> 项目已附带 `0001_initial.py` 初始迁移文件，无需再执行 `makemigrations`。

### 4. 创建超级用户（用于访问 Admin 后台与登录练习 CRUD）

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
| http://127.0.0.1:8000/ | 学生列表首页 |
| http://127.0.0.1:8000/dashboard/ | 统计仪表盘 |
| http://127.0.0.1:8000/student/new/ | 新建学生（需登录） |
| http://127.0.0.1:8000/login/ | 登录 |
| http://127.0.0.1:8000/admin/ | Django Admin 后台 |

## URL 路由总览

| 命名 | URL | 说明 |
| --- | --- | --- |
| `students:student_list` | `/` | 学生列表（分页 + 搜索） |
| `students:student_detail` | `/student/<pk>/` | 学生详情 + 成绩列表 |
| `students:student_create` | `/student/new/` | 新建学生（需登录） |
| `students:student_edit` | `/student/<pk>/edit/` | 编辑学生（需登录） |
| `students:student_delete` | `/student/<pk>/delete/` | 删除学生（需登录） |
| `students:grade_create` | `/student/<pk>/grade/new/` | 为学生添加成绩（需登录） |
| `students:grade_delete` | `/grade/<pk>/delete/` | 删除某条成绩（需登录） |
| `students:dashboard` | `/dashboard/` | 统计仪表盘 |
| `students:login` | `/login/` | 登录 |
| `students:logout` | `/logout/` | 登出 |
| admin | `/admin/` | 后台管理 |

## 权限说明

- **游客**：可浏览学生列表、学生详情、仪表盘；不可新建 / 编辑 / 删除
- **登录用户**：可执行全部 CRUD 操作，包括添加 / 删除成绩
- **超级用户**：拥有所有登录用户权限，并可在 Admin 后台管理所有数据

## 技术要点

- **基于类的视图 (CBV)**：使用 `ListView` / `DetailView` / `CreateView` / `UpdateView` / `DeleteView` 五大通用视图
- **登录保护**：`LoginRequiredMixin` 限制写操作；`login_url` 通过 `LOGIN_URL` 自动重定向
- **搜索与筛选**：在 `get_queryset` 中根据 GET 参数 `q` / `gender` 动态过滤
- **分页**：`paginate_by = 10` + 模板分页控件
- **外键关联**：`Grade.student` 外键 `on_delete=CASCADE`，`related_name='grades'`
- **表单分离**：`StudentForm` / `GradeForm` / `StudentSearchForm` 各司其职
- **模板继承**：`base.html` 抽出公共导航与布局，子模板填充 `content` 块
- **中文本地化**：`LANGUAGE_CODE = 'zh-hans'`，`TIME_ZONE = 'Asia/Shanghai'`

## 扩展思路

- 增加按班级、科目维度的统计图表 (Chart.js)
- 增加 Excel 批量导入 / 导出学生成绩 (`openpyxl`)
- 增加学生头像上传与文件存储
- 增加科目 (Subject) 独立模型，成绩关联科目外键
- 增加 AJAX 局部刷新的成绩录入
- 使用 `django-bootstrap5` 美化表单渲染
