"""
employees 应用 - 初始迁移。

创建 Department（含自引用 parent 外键与 manager 外键到用户），
以及 Employee（OneToOne 用户、FK 部门）。

依赖 accounts/0001_initial（用户模型已创建，但尚未有 department 字段）。
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Department",
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
                (
                    "name",
                    models.CharField(
                        max_length=100, unique=True, verbose_name="部门名称"
                    ),
                ),
                ("description", models.TextField(blank=True, verbose_name="部门描述")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="创建时间"),
                ),
                (
                    "manager",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="managed_departments",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="负责人",
                    ),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="children",
                        to="employees.department",
                        verbose_name="上级部门",
                    ),
                ),
            ],
            options={
                "verbose_name": "部门",
                "verbose_name_plural": "部门",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Employee",
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
                (
                    "position",
                    models.CharField(blank=True, max_length=100, verbose_name="岗位"),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "在职"),
                            ("leave", "休假"),
                            ("resigned", "离职"),
                        ],
                        default="active",
                        max_length=20,
                        verbose_name="状态",
                    ),
                ),
                (
                    "salary",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=10,
                        null=True,
                        verbose_name="薪资",
                    ),
                ),
                (
                    "joined_at",
                    models.DateField(blank=True, null=True, verbose_name="入职日期"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="创建时间"),
                ),
                (
                    "department",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="employees",
                        to="employees.department",
                        verbose_name="所属部门",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="employee_profile",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="用户",
                    ),
                ),
            ],
            options={
                "verbose_name": "员工",
                "verbose_name_plural": "员工",
                "ordering": ["-created_at"],
            },
        ),
    ]
