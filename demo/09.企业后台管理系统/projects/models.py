"""
项目应用 - 项目与任务模型。

包含：
- Project：项目，关联经理、部门、成员，记录状态、预算、周期。
- Task：任务，归属项目，指派给用户，记录状态、优先级、截止时间。
"""

from django.conf import settings
from django.db import models


class Project(models.Model):
    """项目模型。"""

    STATUS_PLANNING = "planning"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_ON_HOLD = "on_hold"
    STATUS_CHOICES = [
        (STATUS_PLANNING, "规划中"),
        (STATUS_IN_PROGRESS, "进行中"),
        (STATUS_COMPLETED, "已完成"),
        (STATUS_ON_HOLD, "已搁置"),
    ]

    name = models.CharField("项目名称", max_length=200)
    code = models.CharField("项目编号", max_length=30, unique=True)
    description = models.TextField("项目描述", blank=True)
    # 项目经理
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="项目经理",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_projects",
    )
    # 所属部门
    department = models.ForeignKey(
        "employees.Department",
        verbose_name="所属部门",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
    )
    # 项目成员
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name="项目成员",
        blank=True,
        related_name="projects",
    )
    status = models.CharField(
        "状态", max_length=20, choices=STATUS_CHOICES, default=STATUS_PLANNING
    )
    start_date = models.DateField("开始日期", null=True, blank=True)
    end_date = models.DateField("结束日期", null=True, blank=True)
    budget = models.DecimalField(
        "预算", max_digits=12, decimal_places=2, null=True, blank=True
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "项目"
        verbose_name_plural = "项目"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Task(models.Model):
    """任务模型。"""

    STATUS_TODO = "todo"
    STATUS_DOING = "doing"
    STATUS_DONE = "done"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_TODO, "待办"),
        (STATUS_DOING, "进行中"),
        (STATUS_DONE, "已完成"),
        (STATUS_CANCELLED, "已取消"),
    ]

    PRIORITY_LOW = "low"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_HIGH = "high"
    PRIORITY_URGENT = "urgent"
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, "低"),
        (PRIORITY_MEDIUM, "中"),
        (PRIORITY_HIGH, "高"),
        (PRIORITY_URGENT, "紧急"),
    ]

    project = models.ForeignKey(
        Project, verbose_name="所属项目", on_delete=models.CASCADE, related_name="tasks"
    )
    title = models.CharField("任务标题", max_length=200)
    description = models.TextField("任务描述", blank=True)
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="负责人",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    status = models.CharField(
        "状态", max_length=20, choices=STATUS_CHOICES, default=STATUS_TODO
    )
    priority = models.CharField(
        "优先级", max_length=10, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM
    )
    due_date = models.DateField("截止日期", null=True, blank=True)
    completed_at = models.DateTimeField("完成时间", null=True, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "任务"
        verbose_name_plural = "任务"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
