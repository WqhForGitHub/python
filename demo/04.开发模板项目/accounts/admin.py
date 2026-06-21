from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """在 Django Admin 中显示自定义字段。"""

    fieldsets = UserAdmin.fieldsets + (
        ('扩展信息', {'fields': ('phone', 'avatar')}),
    )
    list_display = ('username', 'email', 'phone', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'phone')
