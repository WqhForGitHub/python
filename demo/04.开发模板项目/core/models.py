"""core 应用模型。

提供抽象基类 `TimestampedModel`，供其他应用复用创建时间 / 更新时间字段。
本应用本身不创建任何数据表。
"""

from django.db import models


class TimestampedModel(models.Model):
    """抽象基类：提供创建时间与更新时间两个公共字段。

    使用方式：
        class Article(TimestampedModel):
            ...
    """

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        abstract = True
        verbose_name = '带时间戳的模型'
        verbose_name_plural = verbose_name
