"""orders 应用的初始迁移。

创建 Order 与 OrderItem 数据表。
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """orders 应用初始迁移。"""

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('products', '0001_initial'),
    ]

    operations = [
        # 订单主表
        migrations.CreateModel(
            name='Order',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('first_name', models.CharField(max_length=50, verbose_name='名字')),
                ('last_name', models.CharField(max_length=50, verbose_name='姓氏')),
                ('email', models.EmailField(max_length=254, verbose_name='邮箱')),
                ('address', models.CharField(max_length=250, verbose_name='地址')),
                (
                    'postal_code',
                    models.CharField(max_length=20, verbose_name='邮政编码'),
                ),
                ('city', models.CharField(max_length=100, verbose_name='城市')),
                (
                    'total_price',
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=10,
                        verbose_name='总价',
                    ),
                ),
                ('paid', models.BooleanField(default=False, verbose_name='是否已支付')),
                (
                    'created_at',
                    models.DateTimeField(auto_now_add=True, verbose_name='创建时间'),
                ),
                (
                    'updated_at',
                    models.DateTimeField(auto_now=True, verbose_name='更新时间'),
                ),
                (
                    'user',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='orders',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='用户',
                    ),
                ),
            ],
            options={
                'verbose_name': '订单',
                'verbose_name_plural': '订单',
                'ordering': ['-created_at'],
            },
        ),
        # 订单条目表
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'price',
                    models.DecimalField(
                        decimal_places=2, max_digits=10, verbose_name='单价'
                    ),
                ),
                (
                    'quantity',
                    models.PositiveIntegerField(default=1, verbose_name='数量'),
                ),
                (
                    'order',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='items',
                        to='orders.order',
                        verbose_name='所属订单',
                    ),
                ),
                (
                    'product',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='order_items',
                        to='products.product',
                        verbose_name='商品',
                    ),
                ),
            ],
            options={
                'verbose_name': '订单条目',
                'verbose_name_plural': '订单条目',
            },
        ),
    ]
