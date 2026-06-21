"""Accounts forms - 注册与个人资料表单"""

from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class UserRegisterForm(UserCreationForm):
    """用户注册表单，基于内置 UserCreationForm 扩展 email 字段。"""

    email = forms.EmailField(required=False, label="邮箱")

    class Meta:
        model = User
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class ProfileForm(forms.ModelForm):
    """个人资料编辑表单，可修改头像与简介。"""

    class Meta:
        model = User
        fields = ("avatar", "bio", "email")
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "avatar": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
        labels = {
            "avatar": "头像",
            "bio": "个人简介",
            "email": "邮箱",
        }
