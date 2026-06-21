from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
)

from .models import User


class UserRegisterForm(UserCreationForm):
    """用户注册表单。"""

    email = forms.EmailField(label="邮箱", required=True)

    class Meta:
        model = User
        fields = ("username", "email", "phone")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class UserLoginForm(AuthenticationForm):
    """用户登录表单。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class UserProfileForm(forms.ModelForm):
    """用户资料编辑表单。"""

    class Meta:
        model = User
        fields = ("username", "email", "phone", "avatar")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
