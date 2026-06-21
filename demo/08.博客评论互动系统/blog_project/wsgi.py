"""
WSGI 配置，用于传统 WSGI 部署。
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog_project.settings')

application = get_wsgi_application()
