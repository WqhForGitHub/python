from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """自定义用户模型，扩展手机号与头像字段。"""

    phone = models.CharField('手机号', max_length=20, blank=True)
    avatar = models.ImageField('头像', upload_to='avatars/', blank=True, null=True)

    def __str__(self):
        return self.username
