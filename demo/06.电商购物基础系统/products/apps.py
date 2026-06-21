"""products 应用配置。"""

from django.apps import AppConfig


class ProductsConfig(AppConfig):
    """商品应用配置类。"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "products"
    verbose_name = "商品管理"
