"""Accounts views - 注册与个人资料视图"""

from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from .forms import ProfileForm, UserRegisterForm
from .models import User


def register(request):
    """用户注册视图。注册成功后自动登录并跳转看板列表。"""
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # 注册成功后自动登录
            login(request, user)
            return redirect("boards:board_list")
    else:
        form = UserRegisterForm()
    return render(request, "registration/register.html", {"form": form})


def login_view(request):
    """用户登录视图，使用 Django 内置 AuthenticationForm。"""
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("boards:board_list")
    else:
        form = AuthenticationForm()
    return render(request, "registration/login.html", {"form": form})


class ProfileView(LoginRequiredMixin, UpdateView):
    """个人资料编辑视图，仅登录用户可访问。"""

    model = User
    form_class = ProfileForm
    template_name = "accounts/profile.html"
    success_url = reverse_lazy("accounts:profile")

    def get_object(self, queryset=None):
        # 当前登录用户只能编辑自己的资料
        return self.request.user

    def form_valid(self, form):
        from django.contrib import messages

        messages.success(self.request, "个人资料已更新。")
        return super().form_valid(form)
