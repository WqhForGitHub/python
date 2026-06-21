"""学生与成绩的 Admin 后台注册。"""

from django.contrib import admin

from .models import Student, Grade


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """学生模型在 Admin 后台的展示配置。"""

    list_display = (
        "name",
        "student_no",
        "gender",
        "age",
        "class_name",
        "email",
        "created_at",
    )
    list_filter = ("gender", "class_name", "created_at")
    search_fields = ("name", "student_no", "email", "phone")
    ordering = ("-created_at",)


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    """成绩模型在 Admin 后台的展示配置。"""

    list_display = ("student", "subject", "score", "exam_date", "created_at")
    list_filter = ("subject", "exam_date")
    search_fields = ("student__name", "student__student_no", "subject")
    ordering = ("-created_at",)
