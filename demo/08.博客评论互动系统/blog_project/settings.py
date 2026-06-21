"""
Django 项目配置文件 - 博客评论互动系统。
"""
from pathlib import Path

# 基础目录：指向项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 安全密钥（演示用，生产环境务必更换）
SECRET_KEY = 'django-insecure-demo-blog-interactive-change-this-in-production-1234567890'

# 调试模式
DEBUG = True

# 允许的主机
ALLOWED_HOSTS = ['*']

# 已安装应用
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 本地应用
    'accounts',
    'blog',
]

# 中间件
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# 根 URL 配置
ROOT_URLCONF = 'blog_project.urls'

# 模板配置
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
            ],
        },
    },
]

# WSGI / ASGI 入口
WSGI_APPLICATION = 'blog_project.wsgi.application'
ASGI_APPLICATION = 'blog_project.asgi.application'

# 数据库：SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 密码验证器
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

# 国际化
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

# 静态文件
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# 主键字段类型
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 自定义用户模型
AUTH_USER_MODEL = 'accounts.User'

# 登录相关跳转
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'blog:post_list'
LOGOUT_REDIRECT_URL = 'blog:post_list'

# 媒体文件（用户上传）
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'
