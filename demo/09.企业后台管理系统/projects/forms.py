"""
项目应用 - 表单。

包含项目表单、任务表单、项目搜索表单。
"""
from django import forms

from .models import Project, Task


class ProjectForm(forms.ModelForm):
    """项目表单。"""

    class Meta:
        model = Project
        fields = [
            'name', 'code', 'description', 'manager', 'department',
            'members', 'status', 'start_date', 'end_date', 'budget',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'members': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 6}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'budget': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        labels = {
            'name': '项目名称',
            'code': '项目编号',
            'description': '项目描述',
            'manager': '项目经理',
            'department': '所属部门',
            'members': '项目成员',
            'status': '状态',
            'start_date': '开始日期',
            'end_date': '结束日期',
            'budget': '预算',
        }


class TaskForm(forms.ModelForm):
    """任务表单。"""

    class Meta:
        model = Task
        fields = [
            'project', 'title', 'description', 'assignee',
            'status', 'priority', 'due_date',
        ]
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'assignee': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'project': '所属项目',
            'title': '任务标题',
            'description': '任务描述',
            'assignee': '负责人',
            'status': '状态',
            'priority': '优先级',
            'due_date': '截止日期',
        }


class ProjectSearchForm(forms.Form):
    """项目搜索/过滤表单。"""

    q = forms.CharField(
        label='关键字', required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': '搜索项目名称/编号'
        })
    )
    status = forms.ChoiceField(
        label='状态', required=False, choices=[('', '全部状态')] + list(Project.STATUS_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
