"""Blog models - 文章 (Article) 与 评论 (Comment) 模型"""

from django.conf import settings
from django.db import models


class Article(models.Model):
    """文章模型"""

    title = models.CharField('标题', max_length=200)
    body = models.TextField('正文')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='articles',
        verbose_name='作者',
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '文章'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title

    @property
    def excerpt(self):
        """文章摘要：取正文前 100 字符"""
        return self.body[:100] + ('...' if len(self.body) > 100 else '')


class Comment(models.Model):
    """评论模型"""

    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='所属文章',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='评论者',
    )
    body = models.TextField('评论内容')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = '评论'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.author.username} -> {self.article.title}'
