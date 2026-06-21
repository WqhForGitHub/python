"""
账户应用 - 表单
包含用户注册表单与个人资料编辑表单。
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class UserRegisterForm(UserCreationForm):
    """用户注册表单，包含角色选择"""

    class Meta:
        model = User
        fields = ("username", "email", "role")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 角色选择只允许学员/教师（不允许注册管理员）
        self.fields["role"].choices = [
            ("student", "学员"),
            ("teacher", "教师"),
        ]


class ProfileForm(forms.ModelForm):
    """个人资料编辑表单"""

    class Meta:
        model = User
        fields = ("bio", "avatar", "phone", "email")
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4}),
        }
