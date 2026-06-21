"""账户视图。"""
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import UserRegisterForm


class RegisterView(CreateView):
    """用户注册视图。"""

    form_class = UserRegisterForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('products:product_list')

    def form_valid(self, form):
        """注册成功后自动登录用户。"""
        response = super().form_valid(form)
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(self.request, username=username, password=password)
        if user is not None:
            login(self.request, user)
        return response


# 模块级视图别名
register = RegisterView.as_view()
