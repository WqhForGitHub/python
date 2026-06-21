"""
账户应用 - 视图
注册、个人资料编辑，登录/登出使用 Django 内置视图。
"""

from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import View

from .forms import ProfileForm, UserRegisterForm


def register(request):
    """用户注册视图"""
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # 注册成功后自动登录
            login(request, user)
            return redirect("courses:course_list")
    else:
        form = UserRegisterForm()
    return render(request, "registration/register.html", {"form": form})


class ProfileView(LoginRequiredMixin, View):
    """个人资料编辑视图"""

    def get(self, request):
        form = ProfileForm(instance=request.user)
        return render(request, "accounts/profile.html", {"form": form})

    def post(self, request):
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("accounts:profile")
        return render(request, "accounts/profile.html", {"form": form})


# 登录视图（基于 Django 内置 LoginView）
class UserLoginView(LoginView):
    """用户登录视图"""

    template_name = "registration/login.html"


# 登出视图（基于 Django 内置 LogoutView）
class UserLogoutView(LogoutView):
    """用户登出视图"""

    # 登出后跳转由 LOGOUT_REDIRECT_URL 配置控制
    next_page = reverse_lazy("courses:course_list")
