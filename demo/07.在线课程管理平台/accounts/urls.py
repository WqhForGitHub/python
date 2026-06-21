"""
账户应用 - URL 路由
命名空间: accounts
"""

from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    # 注册
    path("register/", views.register, name="register"),
    # 登录
    path("login/", views.UserLoginView.as_view(), name="login"),
    # 登出
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    # 个人资料
    path("profile/", views.ProfileView.as_view(), name="profile"),
]
