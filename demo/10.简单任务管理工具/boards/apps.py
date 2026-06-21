"""Boards app config."""

from django.apps import AppConfig


class BoardsConfig(AppConfig):
    """看板应用配置"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'boards'
    verbose_name = '看板'
