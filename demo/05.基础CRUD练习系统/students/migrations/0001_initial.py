# Generated for 基础CRUD练习系统 (Django Demo)

from django.db import migrations, models


class Migration(migrations.Migration):
    """初始迁移：创建 Student 与 Grade 两张表。"""

    initial = True

    dependencies = []

    operations = [
        # 1. 创建学生表
        migrations.CreateModel(
            name="Student",
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
                ("name", models.CharField(max_length=50, verbose_name="姓名")),
                (
                    "student_no",
                    models.CharField(max_length=20, unique=True, verbose_name="学号"),
                ),
                (
                    "gender",
                    models.CharField(
                        choices=[("male", "男"), ("female", "女"), ("other", "其他")],
                        default="male",
                        max_length=10,
                        verbose_name="性别",
                    ),
                ),
                (
                    "age",
                    models.IntegerField(blank=True, null=True, verbose_name="年龄"),
                ),
                (
                    "email",
                    models.EmailField(blank=True, max_length=254, verbose_name="邮箱"),
                ),
                (
                    "phone",
                    models.CharField(blank=True, max_length=20, verbose_name="电话"),
                ),
                (
                    "class_name",
                    models.CharField(blank=True, max_length=50, verbose_name="班级"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="创建时间"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="更新时间"),
                ),
            ],
            options={
                "verbose_name": "学生",
                "verbose_name_plural": "学生",
                "ordering": ["-created_at"],
            },
        ),
        # 2. 创建成绩表（外键指向 Student）
        migrations.CreateModel(
            name="Grade",
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
                ("subject", models.CharField(max_length=50, verbose_name="科目")),
                ("score", models.FloatField(verbose_name="分数")),
                (
                    "exam_date",
                    models.DateField(blank=True, null=True, verbose_name="考试日期"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="创建时间"),
                ),
                (
                    "student",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        related_name="grades",
                        to="students.student",
                        verbose_name="学生",
                    ),
                ),
            ],
            options={
                "verbose_name": "成绩",
                "verbose_name_plural": "成绩",
                "ordering": ["-created_at"],
            },
        ),
    ]
