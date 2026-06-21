"""商品后台管理。"""

from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """分类后台管理。"""

    list_display = ("id", "name", "description")
    list_filter = ("name",)
    search_fields = ("name", "description")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """商品后台管理。"""

    list_display = (
        "id",
        "name",
        "category",
        "price",
        "stock",
        "is_active",
        "created_at",
    )
    list_filter = ("category", "is_active", "created_at")
    search_fields = ("name", "description")
    list_editable = ("price", "stock", "is_active")
    raw_id_fields = ("category",)
