"""
课程应用 - 表单
包含课程表单与课时表单。
"""
from django import forms

from .models import Course, Lesson


class CourseForm(forms.ModelForm):
    """课程创建/编辑表单"""

    class Meta:
        model = Course
        fields = ('title', 'description', 'category', 'cover', 'price', 'is_published')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        # 接收 request 以便后续可能使用（当前保留以兼容视图调用）
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)


class LessonForm(forms.ModelForm):
    """课时创建表单"""

    class Meta:
        model = Lesson
        fields = ('title', 'content', 'video_url', 'order')
        widgets = {
            'content': forms.Textarea(attrs={'rows': 8}),
        }
