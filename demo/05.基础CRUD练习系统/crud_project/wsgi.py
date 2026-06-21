"""
WSGI config for crud_project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crud_project.settings')

application = get_wsgi_application()
