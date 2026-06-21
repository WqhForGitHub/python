"""Users admin - Django Admin 后台注册"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """自定义用户在 Admin 后台的展示"""

    list_display = (
        "username",
        "email",
        "phone",
        "is_active",
        "is_staff",
        "is_superuser",
        "date_joined",
    )
    list_filter = ("is_active", "is_staff", "is_superuser", "date_joined")
    search_fields = ("username", "email", "phone")
    ordering = ("-date_joined",)

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "扩展信息",
            {
                "fields": ("phone", "avatar", "bio", "date_of_birth"),
            },
        ),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            "扩展信息",
            {
                "fields": ("phone", "avatar", "bio", "date_of_birth"),
            },
        ),
    )
