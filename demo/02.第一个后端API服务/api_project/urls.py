"""URL 配置 - 第一个后端API服务。

路由总览：
    /                     → 重定向到 /api/
    /admin/               → Django Admin 后台
    /api/                 → API 信息
    /api/health/          → 健康检查
    /api/tasks/           → 任务列表 / 创建
    /api/tasks/<int:pk>/  → 任务详情 / 更新 / 删除
"""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', views.api_root, name='api_root'),
    path('api/health/', views.health_check, name='health_check'),
    path('api/tasks/', include('tasks.urls')),
    path('', RedirectView.as_view(url='/api/', permanent=False), name='home'),
]

# 自定义 JSON 错误处理器（DEBUG=False 时生效）
handler404 = 'api_project.views.json_404'
handler500 = 'api_project.views.json_500'
