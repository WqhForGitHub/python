"""boards 初始迁移 - 看板、列、卡片"""

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
            name="Board",
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
                ("title", models.CharField(max_length=200, verbose_name="标题")),
                ("description", models.TextField(blank=True, verbose_name="描述")),
                (
                    "is_archived",
                    models.BooleanField(default=False, verbose_name="已归档"),
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
                    "members",
                    models.ManyToManyField(
                        blank=True,
                        related_name="shared_boards",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="成员",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="boards",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="所有者",
                    ),
                ),
            ],
            options={
                "verbose_name": "看板",
                "verbose_name_plural": "看板",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Column",
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
                ("title", models.CharField(max_length=100, verbose_name="标题")),
                ("order", models.IntegerField(default=0, verbose_name="排序")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="创建时间"),
                ),
                (
                    "board",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="columns",
                        to="boards.board",
                        verbose_name="所属看板",
                    ),
                ),
            ],
            options={
                "verbose_name": "列",
                "verbose_name_plural": "列",
                "ordering": ["order"],
            },
        ),
        migrations.CreateModel(
            name="Card",
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
                ("title", models.CharField(max_length=200, verbose_name="标题")),
                ("description", models.TextField(blank=True, verbose_name="描述")),
                (
                    "labels",
                    models.CharField(
                        blank=True,
                        help_text="多个标签用英文逗号分隔",
                        max_length=200,
                        verbose_name="标签",
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
                ("order", models.IntegerField(default=0, verbose_name="排序")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="创建时间"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="更新时间"),
                ),
                (
                    "assignee",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="cards",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="负责人",
                    ),
                ),
                (
                    "column",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cards",
                        to="boards.column",
                        verbose_name="所属列",
                    ),
                ),
            ],
            options={
                "verbose_name": "卡片",
                "verbose_name_plural": "卡片",
                "ordering": ["order"],
            },
        ),
    ]
