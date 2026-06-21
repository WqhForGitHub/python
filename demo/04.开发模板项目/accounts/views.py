from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from .forms import UserLoginForm, UserProfileForm, UserRegisterForm
from .models import User


class RegisterView(CreateView):
    """用户注册视图。"""

    form_class = UserRegisterForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('core:home')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


class UserLoginView(LoginView):
    """用户登录视图。"""

    form_class = UserLoginForm
    template_name = 'registration/login.html'


class UserLogoutView(LogoutView):
    """用户登出视图。"""

    pass


class ProfileView(LoginRequiredMixin, UpdateView):
    """用户资料编辑视图。"""

    model = User
    form_class = UserProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user


def register(request):
    """函数式注册视图（兼容用法）。"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('core:home')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})
