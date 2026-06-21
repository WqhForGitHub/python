"""
员工应用 - 表单。

包含部门表单、员工表单、员工搜索表单。
"""
from django import forms

from .models import Department, Employee


class DepartmentForm(forms.ModelForm):
    """部门表单。"""

    class Meta:
        model = Department
        fields = ['name', 'manager', 'parent', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'name': '部门名称',
            'manager': '负责人',
            'parent': '上级部门',
            'description': '部门描述',
        }


class EmployeeForm(forms.ModelForm):
    """员工表单。"""

    class Meta:
        model = Employee
        fields = ['user', 'department', 'position', 'status', 'salary', 'joined_at']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'joined_at': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'user': '关联用户',
            'department': '所属部门',
            'position': '岗位',
            'status': '状态',
            'salary': '薪资',
            'joined_at': '入职日期',
        }


class EmployeeSearchForm(forms.Form):
    """员工搜索/过滤表单。"""

    q = forms.CharField(
        label='关键字', required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': '搜索用户名/岗位'
        })
    )
    department = forms.ModelChoiceField(
        label='部门', required=False, queryset=Department.objects.all(),
        empty_label='全部部门',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        label='状态', required=False, choices=[('', '全部状态')] + list(Employee.STATUS_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
