"""账户 URL 路由。"""

from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    # 用户注册
    path("register/", views.register, name="register"),
    # 用户登录
    path(
        "login/",
        LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    # 用户登出
    path("logout/", LogoutView.as_view(), name="logout"),
]
