"""
博客评论互动系统 URL 配置（根路由）。
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 后台管理
    path('admin/', admin.site.urls),
    # 用户认证相关（登录/注册/资料）
    path('accounts/', include('accounts.urls')),
    # 博客应用挂在根路径
    path('', include('blog.urls')),
]

# 开发环境下提供媒体文件访问
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
