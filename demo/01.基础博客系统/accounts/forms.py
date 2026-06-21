"""Custom user registration form."""

from django import forms
from django.contrib.auth.models import User


class UserRegisterForm(forms.ModelForm):
    """用户注册表单"""

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        label="密码",
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        label="确认密码",
    )

    class Meta:
        model = User
        fields = ["username", "email"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }
        labels = {
            "username": "用户名",
            "email": "邮箱",
        }

    def clean_password2(self):
        """校验两次密码一致"""
        password = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")
        if password and password2 and password != password2:
            raise forms.ValidationError("两次输入的密码不一致")
        return password2

    def save(self, commit=True):
        """保存用户，并对密码加密"""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user
