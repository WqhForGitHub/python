"""
账户应用 - 后台管理
注册自定义 User 模型，使用自定义 UserAdmin。
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """自定义用户后台管理"""
    # 列表显示
    list_display = (
        'username', 'email', 'role', 'phone',
        'is_staff', 'is_active',
    )
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'phone')

    # 在编辑页中追加自定义字段
    fieldsets = BaseUserAdmin.fieldsets + (
        ('扩展信息', {
            'fields': ('role', 'bio', 'avatar', 'phone'),
        }),
    )
    # 创建用户时也包含自定义字段
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('扩展信息', {
            'fields': ('role', 'bio', 'avatar', 'phone'),
        }),
    )
