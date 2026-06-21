"""
用户模型 - 扩展 Django 默认用户，增加昵称、头像、个人简介。
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """自定义用户模型。"""

    # 昵称：用于前台显示
    nickname = models.CharField("昵称", max_length=50, blank=True)
    # 头像：上传到 avatars 目录
    avatar = models.ImageField("头像", upload_to="avatars/", blank=True, null=True)
    # 个人简介
    bio = models.TextField("个人简介", blank=True)

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"

    def __str__(self):
        # 优先返回昵称，没有则返回用户名
        return self.nickname or self.username
