"""
template_project URL Configuration

开发模板项目 - 根路由配置

包含 core 应用路由与 Django Admin，并注册自定义 404 / 500 处理器。
"""

from django.contrib import admin
from django.urls import include, path

from core import views as core_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("accounts/", include("accounts.urls")),
]

# 自定义错误处理器
handler404 = "core.views.handler404"
handler500 = "core.views.handler500"
