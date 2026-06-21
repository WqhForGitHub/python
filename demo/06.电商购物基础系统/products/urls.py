"""商品 URL 路由。"""

from django.urls import path

from . import views

app_name = "products"

urlpatterns = [
    # 商品列表（首页）
    path("", views.ProductListView.as_view(), name="product_list"),
    # 商品详情
    path("product/<int:pk>/", views.ProductDetailView.as_view(), name="product_detail"),
]
