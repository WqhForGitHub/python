"""
员工应用 - 部门与员工模型。

包含：
- Department：部门，支持层级（父部门）与负责人。
- Employee：员工，与用户一对一关联，记录岗位、状态、薪资等。
"""

from django.conf import settings
from django.db import models


class Department(models.Model):
    """部门模型。"""

    name = models.CharField("部门名称", max_length=100, unique=True)
    # 部门负责人
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="负责人",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_departments",
    )
    description = models.TextField("部门描述", blank=True)
    # 父部门（层级）
    parent = models.ForeignKey(
        "self",
        verbose_name="上级部门",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "部门"
        verbose_name_plural = "部门"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Employee(models.Model):
    """员工模型（与用户一对一）。"""

    STATUS_ACTIVE = "active"
    STATUS_LEAVE = "leave"
    STATUS_RESIGNED = "resigned"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "在职"),
        (STATUS_LEAVE, "休假"),
        (STATUS_RESIGNED, "离职"),
    ]

    # 关联用户
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name="用户",
        on_delete=models.CASCADE,
        related_name="employee_profile",
    )
    # 所属部门
    department = models.ForeignKey(
        Department,
        verbose_name="所属部门",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
    )
    position = models.CharField("岗位", max_length=100, blank=True)
    status = models.CharField(
        "状态", max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE
    )
    salary = models.DecimalField(
        "薪资", max_digits=10, decimal_places=2, null=True, blank=True
    )
    joined_at = models.DateField("入职日期", null=True, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "员工"
        verbose_name_plural = "员工"
        ordering = ["-created_at"]

    def __str__(self):
        return self.user.username
