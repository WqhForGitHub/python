"""
用户相关表单：注册、资料编辑。
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class UserRegisterForm(UserCreationForm):
    """用户注册表单，基于 UserCreationForm 增加昵称字段。"""

    nickname = forms.CharField(
        label='昵称', max_length=50, required=False,
        help_text='可选，显示在文章和评论中。'
    )

    class Meta:
        model = User
        fields = ('username', 'nickname', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 给 email 字段设置非必填
        self.fields['email'].required = False


class ProfileForm(forms.ModelForm):
    """用户资料编辑表单。"""

    class Meta:
        model = User
        fields = ('nickname', 'email', 'avatar', 'bio')
        labels = {
            'nickname': '昵称',
            'email': '邮箱',
            'avatar': '头像',
            'bio': '个人简介',
        }
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': '介绍一下自己吧...'}),
        }
