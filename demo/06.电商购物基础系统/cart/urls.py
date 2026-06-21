"""购物车 URL 路由。"""

from django.urls import path

from . import views

app_name = "cart"

urlpatterns = [
    # 添加商品到购物车
    path("add/<int:product_id>/", views.cart_add, name="cart_add"),
    # 从购物车移除商品
    path("remove/<int:product_id>/", views.cart_remove, name="cart_remove"),
    # 购物车详情
    path("", views.cart_detail, name="cart_detail"),
]
