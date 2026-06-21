"""
Django settings for template_project.

开发模板项目 - Django Demo

本文件演示一个分离式、可配置的项目设置：
- 通过 os.environ 读取敏感配置（SECRET_KEY / DEBUG / ALLOWED_HOSTS）
- 集成自定义用户模型、自定义中间件、上下文处理器
- 默认使用 SQLite，注释中说明如何切换到 PostgreSQL
"""

import os
from pathlib import Path

# 基础路径：BASE_DIR 指向项目根目录（manage.py 所在目录）
BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# 安全相关配置：优先从环境变量读取，便于多环境部署
# ---------------------------------------------------------------------------

SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-demo-template-project-change-this-in-production-1234567890',
)

DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes', 'on')

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')


# ---------------------------------------------------------------------------
# 应用注册
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 本地应用
    'core',
    'accounts',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 自定义中间件：记录请求耗时
    'core.middleware.RequestTimingMiddleware',
]

ROOT_URLCONF = 'template_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # 自定义上下文处理器：注入站点信息
                'core.context_processors.app_info',
            ],
        },
    },
]

WSGI_APPLICATION = 'template_project.wsgi.application'
ASGI_APPLICATION = 'template_project.asgi.application'


# ---------------------------------------------------------------------------
# 数据库配置
# 默认 SQLite；如需切换为 PostgreSQL，可参考注释中的写法
# ---------------------------------------------------------------------------

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 切换 PostgreSQL 示例（需要 pip install psycopg2-binary）：
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.environ.get('DB_NAME', 'template_db'),
#         'USER': os.environ.get('DB_USER', 'postgres'),
#         'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
#         'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
#         'PORT': os.environ.get('DB_PORT', '5432'),
#     }
# }


# ---------------------------------------------------------------------------
# 密码校验
# ---------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ---------------------------------------------------------------------------
# 国际化
# ---------------------------------------------------------------------------

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_TZ = True


# ---------------------------------------------------------------------------
# 静态文件与媒体文件
# ---------------------------------------------------------------------------

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ---------------------------------------------------------------------------
# 默认主键字段类型
# ---------------------------------------------------------------------------

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ---------------------------------------------------------------------------
# 认证相关
# ---------------------------------------------------------------------------

# 自定义用户模型（强烈建议在项目初期就配置）
AUTH_USER_MODEL = 'accounts.User'

# 登录 / 登出跳转地址
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'core:home'
LOGOUT_REDIRECT_URL = 'core:home'


# ---------------------------------------------------------------------------
# 站点自定义配置
# ---------------------------------------------------------------------------

SITE_NAME = '开发模板项目'
APP_VERSION = '0.1.0'
