"""学生成绩管理的数据模型。"""

from django.db import models


class Student(models.Model):
    """学生模型：保存学生的基本信息。"""

    # 性别选项
    GENDER_CHOICES = [
        ("male", "男"),
        ("female", "女"),
        ("other", "其他"),
    ]

    name = models.CharField("姓名", max_length=50)
    student_no = models.CharField("学号", max_length=20, unique=True)
    gender = models.CharField(
        "性别", max_length=10, choices=GENDER_CHOICES, default="male"
    )
    age = models.IntegerField("年龄", null=True, blank=True)
    email = models.EmailField("邮箱", blank=True)
    phone = models.CharField("电话", max_length=20, blank=True)
    class_name = models.CharField("班级", max_length=50, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "学生"
        verbose_name_plural = "学生"

    def __str__(self):
        return self.name


class Grade(models.Model):
    """成绩模型：一个学生可以有多条成绩记录。"""

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="grades",
        verbose_name="学生",
    )
    subject = models.CharField("科目", max_length=50)
    score = models.FloatField("分数")
    exam_date = models.DateField("考试日期", null=True, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "成绩"
        verbose_name_plural = "成绩"

    def __str__(self):
        return f"{self.student.name} - {self.subject}"
