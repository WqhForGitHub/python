"""Boards admin - 看板、列、卡片后台注册"""

from django.contrib import admin

from .models import Board, Card, Column


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    """看板后台：横向展示成员多选框。"""

    list_display = ("title", "owner", "is_archived", "created_at")
    list_filter = ("is_archived", "created_at")
    search_fields = ("title", "description")
    filter_horizontal = ("members",)
    raw_id_fields = ("owner",)


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    """列后台。"""

    list_display = ("title", "board", "order", "created_at")
    list_filter = ("board",)
    search_fields = ("title",)
    raw_id_fields = ("board",)


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    """卡片后台：展示关键字段并按优先级、列过滤。"""

    list_display = (
        "title",
        "column",
        "assignee",
        "priority",
        "due_date",
        "order",
    )
    list_filter = ("priority", "column__board", "column")
    search_fields = ("title", "description", "labels")
    raw_id_fields = ("column", "assignee")
