"""自定义上下文处理器。

向所有模板注入站点信息（站点名称、应用版本）。
"""

from django.conf import settings


def app_info(request):
    """返回站点信息，供模板直接使用 {{ site_name }} / {{ app_version }}。"""
    return {
        'site_name': getattr(settings, 'SITE_NAME', 'Django 模板项目'),
        'app_version': getattr(settings, 'APP_VERSION', '0.0.0'),
    }
