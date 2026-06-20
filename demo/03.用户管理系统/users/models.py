"""Users models - 自定义用户模型"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """自定义用户模型

    继承 AbstractUser，保留原有用户名/密码/邮箱/权限等字段，
    并扩展电话、头像、简介、注册时间等业务字段。
    """

    email = models.EmailField('邮箱', unique=True)
    phone = models.CharField(
        '手机号',
        max_length=20,
        blank=True,
        default='',
    )
    avatar = models.ImageField(
        '头像',
        upload_to='avatars/',
        blank=True,
        null=True,
    )
    bio = models.TextField('个人简介', blank=True, default='')
    date_of_birth = models.DateField('出生日期', blank=True, null=True)
    created_at = models.DateTimeField('注册时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        ordering = ['-date_joined']
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username

    @property
    def display_name(self):
        """在页面上展示的名称：优先姓全名，其次用户名"""
        full_name = self.get_full_name()
        return full_name if full_name else self.username

    @property
    def avatar_url(self):
        """头像 URL，无头像时返回空字符串"""
        if self.avatar:
            return self.avatar.url
        return ''
