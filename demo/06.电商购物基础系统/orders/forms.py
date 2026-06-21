"""订单相关表单。"""
from django import forms

from .models import Order


class OrderCreateForm(forms.ModelForm):
    """创建订单的表单，收集收货人信息。"""

    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'address', 'postal_code', 'city']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'first_name': '名字',
            'last_name': '姓氏',
            'email': '邮箱',
            'address': '详细地址',
            'postal_code': '邮政编码',
            'city': '城市',
        }
