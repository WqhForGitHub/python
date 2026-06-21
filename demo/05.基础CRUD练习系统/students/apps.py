"""students 应用的应用配置。"""

from django.apps import AppConfig


class StudentsConfig(AppConfig):
    """students 应用的配置类。"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "students"
    verbose_name = "学生成绩管理"
