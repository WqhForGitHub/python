"""
WSGI config for task_project.

简单任务管理工具 - WSGI 入口
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_project.settings')

application = get_wsgi_application()
