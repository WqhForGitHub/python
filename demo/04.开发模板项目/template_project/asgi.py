"""
ASGI config for template_project.

开发模板项目 - ASGI 入口
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'template_project.settings')

application = get_asgi_application()
