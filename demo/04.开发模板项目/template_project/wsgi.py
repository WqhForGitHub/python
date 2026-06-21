"""
WSGI config for template_project.

开发模板项目 - WSGI 入口
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "template_project.settings")

application = get_wsgi_application()
