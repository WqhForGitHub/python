"""students 应用的 URL 路由配置（命名空间 'students'）。"""

from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views

app_name = 'students'

urlpatterns = [
    # 学生列表（首页）
    path('', views.StudentListView.as_view(), name='student_list'),
    # 统计仪表盘
    path('dashboard/', views.dashboard, name='dashboard'),
    # 学生详情
    path('student/<int:pk>/', views.StudentDetailView.as_view(), name='student_detail'),
    # 新建学生
    path('student/new/', views.StudentCreateView.as_view(), name='student_create'),
    # 编辑学生
    path('student/<int:pk>/edit/', views.StudentUpdateView.as_view(), name='student_edit'),
    # 删除学生
    path('student/<int:pk>/delete/', views.StudentDeleteView.as_view(), name='student_delete'),
    # 为学生添加成绩
    path('student/<int:pk>/grade/new/', views.GradeCreateView.as_view(), name='grade_create'),
    # 删除成绩
    path('grade/<int:pk>/delete/', views.grade_delete, name='grade_delete'),
    # 登录 / 登出
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
