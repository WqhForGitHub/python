"""
用户管理后台注册。
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """自定义用户的后台管理界面。"""

    # 列表展示字段
    list_display = ('username', 'nickname', 'email', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'nickname', 'email')

    # 在编辑表单中增加自定义字段
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('个人信息'), {'fields': ('nickname', 'email', 'avatar', 'bio')}),
        (_('权限'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('重要日期'), {'fields': ('last_login', 'date_joined')}),
    )

    # 创建用户时表单
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'nickname', 'email', 'password1', 'password2'),
        }),
    )

    ordering = ('-date_joined',)
