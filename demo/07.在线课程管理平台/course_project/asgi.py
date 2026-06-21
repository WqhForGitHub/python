"""
ASGI 配置 - 在线课程管理平台
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "course_project.settings")

application = get_asgi_application()
