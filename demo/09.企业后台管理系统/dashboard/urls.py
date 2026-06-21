"""
仪表盘应用 - URL 路由。

命名空间：dashboard
"""

from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.index, name="index"),
]
