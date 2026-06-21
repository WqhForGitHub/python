# 电商购物基础系统 (E-commerce Shopping Basic System)

这是一个基于纯 Django 5.x 的电商购物基础系统示例项目，演示了商品目录、购物车、订单与用户认证的基本实现。

## 功能特性

- **商品目录**：分类浏览、搜索、分页、商品详情
- **购物车**：基于 session 的购物车，增删商品、修改数量
- **订单管理**：创建订单、查看订单列表、订单详情
- **用户认证**：注册、登录、登出
- **后台管理**：Django Admin 管理商品、分类、订单

## 技术栈

- Python >= 3.10
- Django >= 5.0（纯 Django，不使用 DRF）
- SQLite 数据库
- Bootstrap 5（CDN）前端样式
- Pillow（处理图片上传）

## 目录结构

```
06.电商购物基础系统/
├── manage.py              # Django 管理脚本
├── requirements.txt       # 依赖清单
├── README.md              # 项目说明
├── .gitignore             # Git 忽略配置
├── shop_project/          # Django 项目配置包
│   ├── __init__.py
│   ├── settings.py        # 项目设置
│   ├── urls.py            # 根 URL 路由
│   ├── wsgi.py            # WSGI 入口
│   └── asgi.py            # ASGI 入口
├── products/              # 商品应用
├── cart/                  # 购物车应用
├── orders/                # 订单应用
├── accounts/              # 账户应用
├── templates/             # 全局模板
└── static/                # 静态文件
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

### 3. 创建超级管理员

```bash
python manage.py createsuperuser
```

### 4. 运行开发服务器

```bash
python manage.py runserver
```

### 5. 访问站点

- 首页商品列表：http://127.0.0.1:8000/
- 后台管理：http://127.0.0.1:8000/admin/
- 登录：http://127.0.0.1:8000/accounts/login/
- 注册：http://127.0.0.1:8000/accounts/register/

## 使用说明

1. 管理员登录后台添加商品分类与商品。
2. 普通用户注册并登录后可浏览商品、加入购物车。
3. 在购物车页面点击「去结算」创建订单。
4. 在「我的订单」页面查看历史订单。

## 说明

本项目为教学演示用途，未包含支付集成与生产环境安全配置，请勿直接用于生产环境。
