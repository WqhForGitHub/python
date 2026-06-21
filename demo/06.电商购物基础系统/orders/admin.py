"""订单后台管理。"""
from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """订单条目内联管理。"""

    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'price', 'quantity')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """订单后台管理。"""

    list_display = (
        'id',
        'user',
        'first_name',
        'last_name',
        'email',
        'city',
        'total_price',
        'paid',
        'created_at',
    )
    list_filter = ('paid', 'created_at', 'city')
    search_fields = ('first_name', 'last_name', 'email', 'address')
    readonly_fields = ('total_price', 'created_at', 'updated_at')
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """订单条目独立管理。"""

    list_display = ('id', 'order', 'product', 'price', 'quantity')
    list_filter = ('product',)
    search_fields = ('order__first_name', 'order__last_name')
