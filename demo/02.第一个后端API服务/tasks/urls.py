"""Tasks URL 路由。

所有路由挂载在 /api/tasks/ 前缀下：
    GET    /api/tasks/           → 任务列表（支持分页、过滤、搜索、排序）
    POST   /api/tasks/           → 创建任务
    GET    /api/tasks/<int:pk>/  → 获取单个任务
    PUT    /api/tasks/<int:pk>/  → 全量更新任务
    PATCH  /api/tasks/<int:pk>/  → 部分更新任务
    DELETE /api/tasks/<int:pk>/  → 删除任务
"""

from django.urls import path

from . import views

app_name = "tasks"

urlpatterns = [
    path("", views.task_list, name="task_list"),
    path("<int:pk>/", views.task_detail, name="task_detail"),
]
