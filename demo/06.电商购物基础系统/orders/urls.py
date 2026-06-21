"""订单 URL 路由。"""

from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    # 创建订单
    path("create/", views.order_create, name="order_create"),
    # 订单详情
    path("<int:pk>/", views.order_detail, name="order_detail"),
    # 订单列表
    path("list/", views.order_list, name="order_list"),
]
