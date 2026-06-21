"""core 应用的应用配置。"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """core 应用配置：公共基础设施（抽象模型、中间件、模板标签等）。"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "公共基础设施"
