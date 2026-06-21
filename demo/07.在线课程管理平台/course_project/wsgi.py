"""
WSGI 配置 - 在线课程管理平台
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "course_project.settings")

application = get_wsgi_application()
