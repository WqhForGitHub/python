"""Accounts admin - 自定义用户后台注册"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """自定义用户的后台展示，增加头像与简介字段。"""

    fieldsets = UserAdmin.fieldsets + (("扩展信息", {"fields": ("avatar", "bio")}),)
    list_display = ("username", "email", "is_staff", "is_active")
    search_fields = ("username", "email")
