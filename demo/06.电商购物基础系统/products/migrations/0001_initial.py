"""products 应用的初始迁移。

创建 Category 与 Product 数据表。
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    """products 应用初始迁移。"""

    initial = True

    dependencies = []

    operations = [
        # 分类表
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        max_length=50, unique=True, verbose_name="分类名称"
                    ),
                ),
                ("description", models.TextField(blank=True, verbose_name="分类描述")),
            ],
            options={
                "verbose_name": "分类",
                "verbose_name_plural": "分类",
            },
        ),
        # 商品表
        migrations.CreateModel(
            name="Product",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=200, verbose_name="商品名称")),
                ("description", models.TextField(blank=True, verbose_name="商品描述")),
                (
                    "price",
                    models.DecimalField(
                        decimal_places=2, max_digits=10, verbose_name="价格"
                    ),
                ),
                ("stock", models.IntegerField(default=0, verbose_name="库存")),
                (
                    "image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to="products/",
                        verbose_name="商品图片",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="是否上架"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="创建时间"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="更新时间"),
                ),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="products",
                        to="products.category",
                        verbose_name="所属分类",
                    ),
                ),
            ],
            options={
                "verbose_name": "商品",
                "verbose_name_plural": "商品",
                "ordering": ["-created_at"],
            },
        ),
    ]
