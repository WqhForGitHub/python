from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """accounts 应用配置。"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
    verbose_name = "用户中心"
