"""cart 应用配置。"""

from django.apps import AppConfig


class CartConfig(AppConfig):
    """购物车应用配置类。"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "cart"
    verbose_name = "购物车"
