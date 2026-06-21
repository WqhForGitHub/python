"""
账户应用 - 表单。

包含用户注册、登录、个人资料编辑表单。
"""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
)

User = get_user_model()


class LoginForm(AuthenticationForm):
    """登录表单。"""

    username = forms.CharField(
        label='用户名', max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入用户名'})
    )
    password = forms.CharField(
        label='密码',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请输入密码'})
    )


class UserRegisterForm(UserCreationForm):
    """用户注册表单。"""

    class Meta:
        model = User
        fields = ('username', 'employee_no', 'email', 'phone', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-control')


class ProfileForm(forms.ModelForm):
    """个人资料编辑表单。"""

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'avatar', 'employee_no')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'avatar': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'employee_no': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }
        labels = {
            'first_name': '姓',
            'last_name': '名',
            'email': '邮箱',
            'phone': '电话',
            'avatar': '头像',
            'employee_no': '员工编号',
        }
