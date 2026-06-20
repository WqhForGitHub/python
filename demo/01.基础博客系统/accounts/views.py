"""Accounts views - 用户注册与登录视图"""

from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.urls import reverse_lazy

from .forms import UserRegisterForm


def register_view(request):
    """用户注册"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # 注册成功后自动登录
            login(request, user)
            return redirect('blog:article_list')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})


def login_view(request):
    """用户登录"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('blog:article_list')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})
