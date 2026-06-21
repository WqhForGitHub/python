"""
task_project URL Configuration

简单任务管理工具 - 根路由
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # 账户应用（注册 / 登录 / 登出 / 个人资料）
    path("accounts/", include("accounts.urls")),
    # 看板应用挂在根路径
    path("", include("boards.urls")),
]
