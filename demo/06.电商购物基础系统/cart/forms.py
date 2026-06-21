"""购物车相关表单。"""

from django import forms


class CartAddProductForm(forms.Form):
    """添加商品到购物车的表单。"""

    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        label="数量",
        widget=forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
    )
    override = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.HiddenInput(),
    )
