"""
课程应用 - 后台管理
注册 Category、Course（含 Lesson 内联）、Lesson、Enrollment。
"""
from django.contrib import admin

from .models import Category, Course, Enrollment, Lesson


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """分类管理"""
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)


class LessonInline(admin.TabularInline):
    """课时内联（在课程编辑页显示）"""
    model = Lesson
    extra = 1
    fields = ('title', 'content', 'video_url', 'order')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """课程管理"""
    list_display = (
        'title', 'category', 'teacher',
        'price', 'is_published', 'created_at',
    )
    list_filter = ('category', 'is_published', 'created_at')
    search_fields = ('title', 'description')
    raw_id_fields = ('teacher',)
    list_editable = ('is_published', 'price')
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """课时管理"""
    list_display = ('title', 'course', 'order', 'created_at')
    list_filter = ('course',)
    search_fields = ('title', 'content')
    ordering = ('course', 'order')


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    """选课记录管理"""
    list_display = ('student', 'course', 'enrolled_at')
    list_filter = ('enrolled_at',)
    search_fields = ('student__username', 'course__title')
    raw_id_fields = ('student', 'course')
    ordering = ('-enrolled_at',)
