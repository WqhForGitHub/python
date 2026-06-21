"""
在线课程管理平台 - 根 URL 配置
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # 后台管理
    path("admin/", admin.site.urls),
    # 账户应用（登录、注册、个人资料）
    path("accounts/", include("accounts.urls", namespace="accounts")),
    # 课程应用（前台课程浏览、选课、课时）
    path("", include("courses.urls", namespace="courses")),
]

# 开发模式下提供媒体文件访问
# 静态文件由 django.contrib.staticfiles 在 DEBUG 模式下自动提供
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
