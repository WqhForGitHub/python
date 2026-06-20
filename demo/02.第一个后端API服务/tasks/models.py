"""Tasks 数据模型 - Task（任务）。"""

from django.db import models


class Task(models.Model):
    """任务模型。"""

    title = models.CharField('标题', max_length=200)
    description = models.TextField('描述', blank=True, default='')
    completed = models.BooleanField('是否完成', default=False)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '任务'
        verbose_name_plural = '任务'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
