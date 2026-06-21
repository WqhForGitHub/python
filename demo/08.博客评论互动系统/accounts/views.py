"""
用户视图：注册、个人资料编辑。
"""
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from .forms import UserRegisterForm, ProfileForm
from .models import User


def register(request):
    """用户注册视图。"""
    if request.user.is_authenticated:
        return redirect('blog:post_list')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # 注册成功后直接登录
            login(request, user)
            return redirect('blog:post_list')
    else:
        form = UserRegisterForm()

    return render(request, 'registration/register.html', {'form': form})


class ProfileView(LoginRequiredMixin, UpdateView):
    """用户资料编辑视图。"""
    model = User
    form_class = ProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        # 当前登录用户
        return self.request.user

    def form_valid(self, form):
        from django.contrib import messages
        messages.success(self.request, '资料已更新。')
        return super().form_valid(form)


# 函数式别名，便于 urls 中使用
profile = ProfileView.as_view()
