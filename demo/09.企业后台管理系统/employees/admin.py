"""
员工应用 - Admin 后台配置。
"""
from django.contrib import admin

from .models import Department, Employee


class EmployeeInline(admin.TabularInline):
    """部门详情页内联展示员工。"""

    model = Employee
    extra = 1
    fk_name = 'department'
    autocomplete_fields = ['user']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """部门 Admin 配置。"""

    list_display = ('name', 'manager', 'parent', 'created_at')
    list_filter = ('parent', 'created_at')
    search_fields = ('name', 'description')
    autocomplete_fields = ['manager', 'parent']
    inlines = [EmployeeInline]
    list_select_related = ('manager', 'parent')


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """员工 Admin 配置。"""

    list_display = (
        'user', 'department', 'position', 'status', 'salary', 'joined_at',
    )
    list_filter = ('status', 'department', 'joined_at')
    search_fields = ('user__username', 'position', 'user__first_name', 'user__last_name')
    raw_id_fields = ('user',)
    list_select_related = ('user', 'department')
    list_editable = ('status',)
