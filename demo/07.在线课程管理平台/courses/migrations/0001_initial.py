"""
课程应用 - 初始迁移
创建 Category、Course、Lesson、Enrollment 模型。
依赖于 accounts 应用的初始迁移（FK 指向用户模型）。
"""

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 1. 分类
        migrations.CreateModel(
            name="Category",
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
                        max_length=50, unique=True, verbose_name="分类名称"
                    ),
                ),
                ("description", models.TextField(blank=True, verbose_name="分类描述")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="创建时间"),
                ),
            ],
            options={
                "verbose_name": "分类",
                "verbose_name_plural": "分类",
                "ordering": ["name"],
            },
        ),
        # 2. 课程
        migrations.CreateModel(
            name="Course",
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
                ("title", models.CharField(max_length=200, verbose_name="课程标题")),
                ("description", models.TextField(verbose_name="课程描述")),
                (
                    "cover",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to="course_covers/",
                        verbose_name="课程封面",
                    ),
                ),
                (
                    "price",
                    models.DecimalField(
                        decimal_places=2, default=0, max_digits=10, verbose_name="价格"
                    ),
                ),
                (
                    "is_published",
                    models.BooleanField(default=False, verbose_name="已发布"),
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
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="courses",
                        to="courses.category",
                        verbose_name="分类",
                    ),
                ),
                (
                    "teacher",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="taught_courses",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="教师",
                    ),
                ),
            ],
            options={
                "verbose_name": "课程",
                "verbose_name_plural": "课程",
                "ordering": ["-created_at"],
            },
        ),
        # 3. 课时
        migrations.CreateModel(
            name="Lesson",
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
                ("title", models.CharField(max_length=200, verbose_name="课时标题")),
                ("content", models.TextField(verbose_name="课时内容")),
                (
                    "video_url",
                    models.URLField(blank=True, null=True, verbose_name="视频链接"),
                ),
                ("order", models.IntegerField(default=0, verbose_name="排序")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="创建时间"),
                ),
                (
                    "course",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lessons",
                        to="courses.course",
                        verbose_name="所属课程",
                    ),
                ),
            ],
            options={
                "verbose_name": "课时",
                "verbose_name_plural": "课时",
                "ordering": ["order"],
            },
        ),
        # 4. 选课记录
        migrations.CreateModel(
            name="Enrollment",
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
                    "enrolled_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="选课时间"),
                ),
                (
                    "course",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="enrollments",
                        to="courses.course",
                        verbose_name="课程",
                    ),
                ),
                (
                    "student",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="enrollments",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="学员",
                    ),
                ),
            ],
            options={
                "verbose_name": "选课记录",
                "verbose_name_plural": "选课记录",
                "unique_together": {("course", "student")},
            },
        ),
    ]
