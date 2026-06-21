"""订单视图。"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View

from cart.cart import Cart

from .forms import OrderCreateForm
from .models import Order, OrderItem


class OrderCreateView(LoginRequiredMixin, View):
    """创建订单视图。

    GET 展示订单表单与购物车摘要；POST 从购物车创建订单。
    """

    def get(self, request):
        """展示订单创建表单。"""
        cart = Cart(request)
        if len(cart) == 0:
            return redirect('cart:cart_detail')
        form = OrderCreateForm()
        # 预填登录用户的邮箱与姓名
        if request.user.is_authenticated:
            form.fields['email'].initial = request.user.email
        return render(
            request,
            'orders/order_create.html',
            {'cart': cart, 'form': form},
        )

    def post(self, request):
        """提交订单，生成订单与订单条目。"""
        cart = Cart(request)
        if len(cart) == 0:
            return redirect('cart:cart_detail')
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            # 创建订单但不立即提交，需关联用户与总价
            order = form.save(commit=False)
            order.user = request.user
            order.total_price = cart.get_total_price()
            order.save()
            # 遍历购物车条目创建订单明细
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    price=item['product'].price,
                    quantity=item['quantity'],
                )
            # 清空购物车
            cart.clear()
            return redirect('orders:order_detail', pk=order.id)
        return render(
            request,
            'orders/order_create.html',
            {'cart': cart, 'form': form},
        )


class OrderDetailView(LoginRequiredMixin, View):
    """订单详情视图。"""

    def get(self, request, pk):
        """展示订单详情，仅允许查看本人订单。"""
        order = get_object_or_404(Order, pk=pk, user=request.user)
        return render(request, 'orders/order_detail.html', {'order': order})


class OrderListView(LoginRequiredMixin, View):
    """订单列表视图，展示当前用户的全部订单。"""

    def get(self, request):
        """展示用户订单列表。"""
        orders = Order.objects.filter(user=request.user)
        return render(request, 'orders/order_list.html', {'orders': orders})


# 模块级 url 友好的视图别名
order_create = OrderCreateView.as_view()
order_detail = OrderDetailView.as_view()
order_list = OrderListView.as_view()
