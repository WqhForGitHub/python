"""
projects 应用 - 初始迁移。

创建 Project（含 manager FK、department FK、members M2M），
以及 Task（含 project FK、assignee FK）。

依赖 accounts/0001_initial 与 employees/0001_initial。
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
        ("employees", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Project",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=200, verbose_name="项目名称")),
                (
                    "code",
                    models.CharField(
                        max_length=30, unique=True, verbose_name="项目编号"
                    ),
                ),
                ("description", models.TextField(blank=True, verbose_name="项目描述")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("planning", "规划中"),
                            ("in_progress", "进行中"),
                            ("completed", "已完成"),
                            ("on_hold", "已搁置"),
                        ],
                        default="planning",
                        max_length=20,
                        verbose_name="状态",
                    ),
                ),
                (
                    "start_date",
                    models.DateField(blank=True, null=True, verbose_name="开始日期"),
                ),
                (
                    "end_date",
                    models.DateField(blank=True, null=True, verbose_name="结束日期"),
                ),
                (
                    "budget",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=12,
                        null=True,
                        verbose_name="预算",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="创建时间"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="更新时间"),
                ),
                (
                    "department",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="projects",
                        to="employees.department",
                        verbose_name="所属部门",
                    ),
                ),
                (
                    "manager",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="managed_projects",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="项目经理",
                    ),
                ),
                (
                    "members",
                    models.ManyToManyField(
                        blank=True,
                        related_name="projects",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="项目成员",
                    ),
                ),
            ],
            options={
                "verbose_name": "项目",
                "verbose_name_plural": "项目",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Task",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=200, verbose_name="任务标题")),
                ("description", models.TextField(blank=True, verbose_name="任务描述")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("todo", "待办"),
                            ("doing", "进行中"),
                            ("done", "已完成"),
                            ("cancelled", "已取消"),
                        ],
                        default="todo",
                        max_length=20,
                        verbose_name="状态",
                    ),
                ),
                (
                    "priority",
                    models.CharField(
                        choices=[
                            ("low", "低"),
                            ("medium", "中"),
                            ("high", "高"),
                            ("urgent", "紧急"),
                        ],
                        default="medium",
                        max_length=10,
                        verbose_name="优先级",
                    ),
                ),
                (
                    "due_date",
                    models.DateField(blank=True, null=True, verbose_name="截止日期"),
                ),
                (
                    "completed_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="完成时间"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="创建时间"),
                ),
                (
                    "assignee",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="tasks",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="负责人",
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tasks",
                        to="projects.project",
                        verbose_name="所属项目",
                    ),
                ),
            ],
            options={
                "verbose_name": "任务",
                "verbose_name_plural": "任务",
                "ordering": ["-created_at"],
            },
        ),
    ]
