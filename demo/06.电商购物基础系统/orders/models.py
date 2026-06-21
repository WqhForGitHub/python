"""订单数据模型。"""
from django.conf import settings
from django.db import models


class Order(models.Model):
    """订单主模型。"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='用户',
    )
    first_name = models.CharField('名字', max_length=50)
    last_name = models.CharField('姓氏', max_length=50)
    email = models.EmailField('邮箱')
    address = models.CharField('地址', max_length=250)
    postal_code = models.CharField('邮政编码', max_length=20)
    city = models.CharField('城市', max_length=100)
    total_price = models.DecimalField('总价', max_digits=10, decimal_places=2, default=0)
    paid = models.BooleanField('是否已支付', default=False)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '订单'
        verbose_name_plural = '订单'
        ordering = ['-created_at']

    def __str__(self):
        return f'订单 #{self.id}'


class OrderItem(models.Model):
    """订单条目模型。"""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='所属订单',
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='order_items',
        verbose_name='商品',
    )
    price = models.DecimalField('单价', max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField('数量', default=1)

    class Meta:
        verbose_name = '订单条目'
        verbose_name_plural = '订单条目'

    def __str__(self):
        return f'{self.id}'

    def get_cost(self):
        """返回该条目的总价。"""
        return self.price * self.quantity
