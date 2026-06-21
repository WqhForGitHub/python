"""orders 应用配置。"""
from django.apps import AppConfig


class OrdersConfig(AppConfig):
    """订单应用配置类。"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'
    verbose_name = '订单管理'
