"""
课程应用 - URL 路由
命名空间: courses
"""
from django.urls import path

from . import views

app_name = 'courses'

urlpatterns = [
    # 课程列表（首页）
    path('', views.course_list, name='course_list'),
    # 我的课程
    path('my/', views.MyCoursesView.as_view(), name='my_courses'),
    # 创建课程
    path('create/', views.CourseCreateView.as_view(), name='course_create'),
    # 课程详情
    path('<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    # 编辑课程
    path('<int:pk>/edit/', views.CourseEditView.as_view(), name='course_edit'),
    # 选课
    path('<int:pk>/enroll/', views.EnrollView.as_view(), name='enroll'),
    # 添加课时
    path('<int:course_pk>/lesson/new/', views.LessonCreateView.as_view(), name='lesson_create'),
    # 课时详情
    path('<int:course_pk>/lesson/<int:pk>/', views.LessonDetailView.as_view(), name='lesson_detail'),
]
