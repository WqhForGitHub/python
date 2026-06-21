"""Django 项目设置文件。"""

from pathlib import Path

# 基础目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 安全密钥（演示用，生产环境请替换）
SECRET_KEY = "django-insecure-demo-ecommerce-shop-change-this-in-production-1234567890"

# 调试模式
DEBUG = True

# 允许的主机
ALLOWED_HOSTS = ["*"]

# 已安装的应用
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 本地应用
    "products",
    "cart",
    "orders",
    "accounts",
]

# 中间件
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# 根 URL 配置
ROOT_URLCONF = "shop_project.urls"

# 模板配置
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # 注入购物车商品数量到模板上下文
                "cart.context_processors.cart_processor",
            ],
        },
    },
]

# WSGI 入口
WSGI_APPLICATION = "shop_project.wsgi.application"

# 数据库配置（SQLite）
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# 密码验证
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# 国际化
LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

# 静态文件
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

# 媒体文件
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# 主键字段类型
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# 登录相关配置
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "products:product_list"
LOGOUT_REDIRECT_URL = "products:product_list"

# 会话配置：购物车依赖 session，设置一天有效期
SESSION_COOKIE_AGE = 86400
