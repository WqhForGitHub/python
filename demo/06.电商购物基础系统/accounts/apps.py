"""accounts 应用配置。"""
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """账户应用配置类。"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = '账户'
