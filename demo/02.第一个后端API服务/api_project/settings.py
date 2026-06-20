"""Django 项目配置 - 第一个后端API服务。"""

from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# 安全配置
# ============================================================
# 仅供开发演示使用，生产环境务必通过环境变量设置强随机密钥
SECRET_KEY = 'django-insecure-9k7^2zq1$lj!@#xmp8w4e&r6bt3yc5ua0hdfovgisn='

DEBUG = True

ALLOWED_HOSTS = ['*']

# ============================================================
# 应用
# ============================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 本地应用
    'tasks',
]

# ============================================================
# 中间件
# ============================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'api_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'api_project.wsgi.application'
ASGI_APPLICATION = 'api_project.asgi.application'

# ============================================================
# 数据库
# ============================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ============================================================
# 密码校验
# ============================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ============================================================
# 国际化与时区
# ============================================================
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

# ============================================================
# 静态文件
# ============================================================
STATIC_URL = '/static/'

# ============================================================
# 默认主键字段类型
# ============================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================
# 分页默认值
# ============================================================
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100
