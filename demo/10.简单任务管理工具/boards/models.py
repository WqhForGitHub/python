"""Boards models - 看板、列、卡片数据模型"""

from django.conf import settings
from django.db import models


class Board(models.Model):
    """看板：任务管理的顶层容器，包含多个列（列表）。"""

    title = models.CharField('标题', max_length=200)
    description = models.TextField('描述', blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='boards',
        verbose_name='所有者',
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='shared_boards',
        verbose_name='成员',
    )
    is_archived = models.BooleanField('已归档', default=False)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '看板'
        verbose_name_plural = '看板'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Column(models.Model):
    """列（列表）：看板中的一列，包含多张卡片。"""

    board = models.ForeignKey(
        Board,
        on_delete=models.CASCADE,
        related_name='columns',
        verbose_name='所属看板',
    )
    title = models.CharField('标题', max_length=100)
    order = models.IntegerField('排序', default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '列'
        verbose_name_plural = '列'
        ordering = ['order']

    def __str__(self):
        return f'{self.board.title} - {self.title}'


class Card(models.Model):
    """卡片：列中的一张任务卡片。"""

    PRIORITY_CHOICES = [
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
        ('urgent', '紧急'),
    ]

    column = models.ForeignKey(
        Column,
        on_delete=models.CASCADE,
        related_name='cards',
        verbose_name='所属列',
    )
    title = models.CharField('标题', max_length=200)
    description = models.TextField('描述', blank=True)
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='cards',
        verbose_name='负责人',
    )
    labels = models.CharField(
        '标签',
        max_length=200,
        blank=True,
        help_text='多个标签用英文逗号分隔',
    )
    priority = models.CharField(
        '优先级',
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
    )
    due_date = models.DateField('截止日期', null=True, blank=True)
    order = models.IntegerField('排序', default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '卡片'
        verbose_name_plural = '卡片'
        ordering = ['order']

    def __str__(self):
        return self.title

    @property
    def label_list(self):
        """将逗号分隔的标签字符串拆分为列表。"""
        if not self.labels:
            return []
        return [label.strip() for label in self.labels.split(',') if label.strip()]
