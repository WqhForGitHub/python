"""
WSGI 配置 - 企业后台管理系统。
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin_project.settings')

application = get_wsgi_application()
