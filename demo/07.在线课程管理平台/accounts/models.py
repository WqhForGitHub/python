"""
账户应用 - 用户模型
自定义 User 模型，扩展角色、简介、头像、电话字段。
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """自定义用户模型，支持学员/教师/管理员角色"""

    class Role(models.TextChoices):
        STUDENT = "student", "学员"
        TEACHER = "teacher", "教师"
        ADMIN = "admin", "管理员"

    # 角色
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        verbose_name="角色",
    )
    # 个人简介
    bio = models.TextField(blank=True, verbose_name="个人简介")
    # 头像
    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
        verbose_name="头像",
    )
    # 联系电话
    phone = models.CharField(max_length=20, blank=True, verbose_name="电话")

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"

    def __str__(self):
        return self.username

    @property
    def is_student(self):
        """是否为学员"""
        return self.role == self.Role.STUDENT

    @property
    def is_teacher(self):
        """是否为教师"""
        return self.role == self.Role.TEACHER
