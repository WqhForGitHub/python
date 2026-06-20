"""Accounts admin - 使用 Django 自带 User，可在此扩展显示"""

from django.contrib import admin
from django.contrib.auth.models import User

# 直接使用 Django 自带的 User 模型，无需额外注册
admin.site.unregister(User)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('username', 'email')
