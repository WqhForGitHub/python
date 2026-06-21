"""
URL configuration for crud_project.

基础CRUD练习系统的根路由配置。
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    # 学生与成绩相关的全部路由挂在根路径下
    path("", include("students.urls")),
]
