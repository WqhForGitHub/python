"""Tasks Admin 后台注册。"""

from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """任务管理后台。"""

    list_display = ('id', 'title', 'completed', 'created_at', 'updated_at')
    list_display_links = ('id', 'title')
    list_filter = ('completed',)
    search_fields = ('title', 'description')
    list_editable = ('completed',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
