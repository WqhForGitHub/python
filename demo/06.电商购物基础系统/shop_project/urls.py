"""项目根 URL 路由配置。"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # 后台管理
    path('admin/', admin.site.urls),
    # 商品应用（首页）
    path('', include('products.urls')),
    # 购物车应用
    path('cart/', include('cart.urls')),
    # 订单应用
    path('orders/', include('orders.urls')),
    # 账户应用
    path('accounts/', include('accounts.urls')),
]

# 开发环境下提供媒体文件访问
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
