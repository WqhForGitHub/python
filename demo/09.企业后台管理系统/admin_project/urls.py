"""
企业后台管理系统 - 根 URL 路由配置。
"""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    # Django Admin 后台
    path("admin/", admin.site.urls),
    # 仪表盘（首页）
    path("", include("dashboard.urls")),
    # 员工与部门管理
    path("employees/", include("employees.urls")),
    # 项目与任务管理
    path("projects/", include("projects.urls")),
    # 账户（登录/登出/个人资料）
    path("accounts/", include("accounts.urls")),
]
