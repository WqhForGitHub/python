"""基于 session 的购物车实现。"""
from decimal import Decimal

from products.models import Product


class Cart:
    """购物车类，数据存储在用户 session 中。

    session 中的购物车结构为：
        request.session['cart'] = {product_id: quantity, ...}
    其中 product_id 为字符串形式的商品主键，quantity 为整数。
    """

    def __init__(self, request):
        """初始化购物车，从 session 中读取已有数据。"""
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            # 初始化空购物车
            cart = self.session['cart'] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        """向购物车中添加商品或修改数量。

        :param product: 商品对象
        :param quantity: 数量
        :param override_quantity: 为 True 时直接覆盖数量，否则累加
        """
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = 0
        if override_quantity:
            self.cart[product_id] = quantity
        else:
            self.cart[product_id] += quantity
        self.save()

    def remove(self, product):
        """从购物车中移除商品。"""
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        """迭代购物车商品，附加商品对象与单项总价。

        每个条目为字典，包含：
            product: 商品对象
            quantity: 数量
            total_price: 该项总价（Decimal）
        """
        product_ids = self.cart.keys()
        # 一次性查询所有商品对象，避免 N+1 查询
        products = Product.objects.filter(id__in=product_ids)
        for product in products:
            quantity = self.cart[str(product.id)]
            yield {
                'product': product,
                'quantity': quantity,
                'total_price': product.price * quantity,
            }

    def __len__(self):
        """返回购物车中商品的总数量（件数之和）。"""
        return sum(self.cart.values())

    def get_total_price(self):
        """返回购物车所有商品的总价。"""
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        product_price_map = {p.id: p.price for p in products}
        total = Decimal('0')
        for product_id, quantity in self.cart.items():
            price = product_price_map.get(int(product_id), Decimal('0'))
            total += price * quantity
        return total

    def clear(self):
        """清空购物车。"""
        del self.session['cart']
        self.save()

    def save(self):
        """标记 session 已修改以持久化。"""
        self.session.modified = True
