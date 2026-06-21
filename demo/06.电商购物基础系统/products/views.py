"""商品视图。"""

from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView, ListView

from cart.forms import CartAddProductForm

from .models import Category, Product


class ProductListView(ListView):
    """商品列表视图，支持分类筛选与搜索。"""

    model = Product
    template_name = "products/product_list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        """根据查询参数过滤商品。"""
        queryset = Product.objects.filter(is_active=True)
        # 分类筛选
        category_id = self.request.GET.get("category")
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        # 关键字搜索
        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(name__icontains=query)
        return queryset

    def get_context_data(self, **kwargs):
        """向模板注入分类列表与当前查询参数。"""
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["current_category"] = self.request.GET.get("category", "")
        context["query"] = self.request.GET.get("q", "")
        return context


class ProductDetailView(DetailView):
    """商品详情视图。"""

    model = Product
    template_name = "products/product_detail.html"
    context_object_name = "product"

    def get_queryset(self):
        """仅展示上架商品。"""
        return Product.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        """向模板注入加入购物车表单。"""
        context = super().get_context_data(**kwargs)
        context["cart_add_form"] = CartAddProductForm()
        return context
