"""
项目应用 - Admin 后台配置。
"""

from django.contrib import admin

from .models import Project, Task


class TaskInline(admin.TabularInline):
    """项目详情页内联展示任务。"""

    model = Task
    extra = 1
    fk_name = "project"
    autocomplete_fields = ["assignee"]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """项目 Admin 配置。"""

    list_display = (
        "name",
        "code",
        "manager",
        "department",
        "status",
        "start_date",
        "end_date",
        "budget",
    )
    list_filter = ("status", "department", "created_at")
    search_fields = ("name", "code", "description")
    filter_horizontal = ("members",)
    autocomplete_fields = ["manager", "department"]
    list_select_related = ("manager", "department")
    list_editable = ("status",)
    inlines = [TaskInline]
    date_hierarchy = "created_at"


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """任务 Admin 配置。"""

    list_display = (
        "title",
        "project",
        "assignee",
        "status",
        "priority",
        "due_date",
    )
    list_filter = ("status", "priority", "project")
    search_fields = ("title", "description")
    autocomplete_fields = ["project", "assignee"]
    list_select_related = ("project", "assignee")
    list_editable = ("status", "priority")
