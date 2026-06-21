"""
项目应用 - URL 路由。

命名空间：projects
"""
from django.urls import path

from . import views

app_name = 'projects'

urlpatterns = [
    # 项目管理
    path('', views.ProjectListView.as_view(), name='project_list'),
    path('new/', views.ProjectCreateView.as_view(), name='project_create'),
    path('<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_edit'),
    path('<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),
    # 任务管理
    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('tasks/new/', views.TaskCreateView.as_view(), name='task_create'),
    path('tasks/<int:pk>/edit/', views.TaskUpdateView.as_view(), name='task_edit'),
    path('tasks/<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),
    path('tasks/<int:pk>/toggle/', views.task_toggle_status, name='task_toggle'),
]
