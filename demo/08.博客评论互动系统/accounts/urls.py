"""
accounts 应用 URL 路由，命名空间 'accounts'。
"""
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    # 注册
    path('register/', views.register, name='register'),
    # 登录（使用 Django 内置视图，自定义模板）
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    # 登出
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    # 个人资料
    path('profile/', views.profile, name='profile'),
]
