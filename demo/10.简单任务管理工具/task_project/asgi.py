"""
ASGI config for task_project.

简单任务管理工具 - ASGI 入口
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "task_project.settings")

application = get_asgi_application()
