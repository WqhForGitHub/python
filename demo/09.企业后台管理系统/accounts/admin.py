"""
账户应用 - Admin 后台配置。

自定义 UserAdmin 以展示扩展字段。
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """自定义用户 Admin 配置。"""

    list_display = (
        'username', 'employee_no', 'get_full_name', 'department',
        'role', 'phone', 'is_active', 'is_staff', 'is_superuser',
    )
    list_filter = ('role', 'department', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'employee_no', 'first_name', 'last_name', 'phone')
    list_select_related = ('department',)

    # 在编辑页中按字段集组织
    fieldsets = BaseUserAdmin.fieldsets + (
        ('企业信息', {
            'fields': (
                'employee_no', 'department', 'role', 'phone',
                'avatar', 'hire_date',
            ),
        }),
    )

    # 新增用户时也包含企业信息
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('企业信息', {
            'fields': (
                'employee_no', 'department', 'role', 'phone', 'hire_date',
            ),
        }),
    )

    autocomplete_fields = ['department']
