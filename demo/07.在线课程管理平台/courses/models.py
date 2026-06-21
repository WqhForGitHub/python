"""
课程应用 - 数据模型
包含分类(Category)、课程(Course)、课时(Lesson)、选课记录(Enrollment)。
"""

from django.conf import settings
from django.db import models


class Category(models.Model):
    """课程分类"""

    name = models.CharField(max_length=50, unique=True, verbose_name="分类名称")
    description = models.TextField(blank=True, verbose_name="分类描述")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "分类"
        verbose_name_plural = "分类"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Course(models.Model):
    """课程"""

    title = models.CharField(max_length=200, verbose_name="课程标题")
    description = models.TextField(verbose_name="课程描述")
    # 分类，可为空，删除分类时置空
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses",
        verbose_name="分类",
    )
    # 教师，可为空，删除教师时置空
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="taught_courses",
        verbose_name="教师",
    )
    # 课程封面
    cover = models.ImageField(
        upload_to="course_covers/",
        blank=True,
        null=True,
        verbose_name="课程封面",
    )
    # 价格
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="价格",
    )
    # 是否发布
    is_published = models.BooleanField(default=False, verbose_name="已发布")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "课程"
        verbose_name_plural = "课程"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Lesson(models.Model):
    """课时"""

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="lessons",
        verbose_name="所属课程",
    )
    title = models.CharField(max_length=200, verbose_name="课时标题")
    content = models.TextField(verbose_name="课时内容")
    video_url = models.URLField(blank=True, null=True, verbose_name="视频链接")
    order = models.IntegerField(default=0, verbose_name="排序")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "课时"
        verbose_name_plural = "课时"
        ordering = ["order"]

    def __str__(self):
        return self.title


class Enrollment(models.Model):
    """选课记录"""

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name="课程",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name="学员",
    )
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name="选课时间")

    class Meta:
        verbose_name = "选课记录"
        verbose_name_plural = "选课记录"
        unique_together = ["course", "student"]

    def __str__(self):
        return f"{self.student} -> {self.course}"
