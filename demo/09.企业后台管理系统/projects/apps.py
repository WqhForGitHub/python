"""projects 应用配置。"""
from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    """项目与任务应用配置。"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'projects'
    verbose_name = '项目管理'
