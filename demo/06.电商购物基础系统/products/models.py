"""商品数据模型。"""
from django.db import models


class Category(models.Model):
    """商品分类模型。"""

    name = models.CharField('分类名称', max_length=50, unique=True)
    description = models.TextField('分类描述', blank=True)

    class Meta:
        verbose_name = '分类'
        verbose_name_plural = '分类'

    def __str__(self):
        return self.name


class Product(models.Model):
    """商品模型。"""

    name = models.CharField('商品名称', max_length=200)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name='所属分类',
    )
    description = models.TextField('商品描述', blank=True)
    price = models.DecimalField('价格', max_digits=10, decimal_places=2)
    stock = models.IntegerField('库存', default=0)
    image = models.ImageField('商品图片', upload_to='products/', blank=True, null=True)
    is_active = models.BooleanField('是否上架', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '商品'
        verbose_name_plural = '商品'
        ordering = ['-created_at']

    def __str__(self):
        return self.name
