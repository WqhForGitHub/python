"""
账户应用 - 视图。

包含自定义登录、登出、个人资料编辑视图。
"""
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from .forms import LoginForm, ProfileForm
from .models import User


def login_view(request):
    """自定义登录视图。"""
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages_success(request, '登录成功，欢迎回来！')
            next_url = request.GET.get('next') or request.POST.get('next')
            return redirect(next_url or 'dashboard:index')
    else:
        form = LoginForm(request)
    return render(request, 'accounts/login.html', {'form': form})


def messages_success(request, msg):
    """简便添加成功消息。"""
    from django.contrib import messages
    messages.success(request, msg)


def logout_view(request):
    """登出视图。"""
    logout(request)
    return redirect('accounts:login')


class ProfileView(LoginRequiredMixin, UpdateView):
    """个人资料编辑视图。"""

    model = User
    form_class = ProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        from django.contrib import messages
        messages.success(self.request, '个人资料已更新。')
        return super().form_valid(form)


# 函数式别名，便于 urls.py 引用
profile = ProfileView.as_view()
