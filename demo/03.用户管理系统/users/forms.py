"""Users forms - 注册 / 个人资料 / 管理员编辑用户"""

from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    UserCreationForm,
)

from .models import User


class UserRegisterForm(UserCreationForm):
    """用户注册表单

    基于 Django 内置 UserCreationForm，额外暴露邮箱字段。
    """

    email = forms.EmailField(
        label='邮箱',
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'username': '用户名',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 为密码字段统一加上 Bootstrap 样式
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].label = '密码'
        self.fields['password2'].label = '确认密码'

    def clean_email(self):
        """邮箱唯一性校验"""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('该邮箱已被注册')
        return email


class LoginForm(AuthenticationForm):
    """登录表单 - 仅增加 Bootstrap 样式"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password'].widget.attrs.update({'class': 'form-control'})


class ProfileForm(forms.ModelForm):
    """用户编辑个人资料表单（不可改用户名）"""

    class Meta:
        model = User
        fields = ['email', 'phone', 'avatar', 'bio', 'date_of_birth']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'avatar': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'date_of_birth': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
            ),
        }
        labels = {
            'email': '邮箱',
            'phone': '手机号',
            'avatar': '头像',
            'bio': '个人简介',
            'date_of_birth': '出生日期',
        }


class UserAdminForm(forms.ModelForm):
    """管理员新建 / 编辑用户表单"""

    password = forms.CharField(
        label='密码',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text='留空则保持原密码不变；新建用户时请填写密码。',
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'phone', 'is_active',
            'is_staff', 'is_superuser', 'bio', 'date_of_birth',
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date_of_birth': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
            ),
        }
        labels = {
            'username': '用户名',
            'email': '邮箱',
            'phone': '手机号',
            'is_active': '是否启用',
            'is_staff': '是否员工(可登录后台)',
            'is_superuser': '是否超级管理员',
            'bio': '个人简介',
            'date_of_birth': '出生日期',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 编辑场景下密码可选；新建场景下密码必填
        if not self.instance.pk:
            self.fields['password'].required = True

    def save(self, commit=True):
        """保存时若有密码则用 set_password 加密"""
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


class CustomPasswordChangeForm(PasswordChangeForm):
    """修改密码表单 - 增加 Bootstrap 样式"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ['old_password', 'new_password1', 'new_password2']:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})
