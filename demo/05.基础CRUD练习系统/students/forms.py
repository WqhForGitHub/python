"""学生成绩管理系统的表单定义。"""

from django import forms

from .models import Student, Grade


class StudentForm(forms.ModelForm):
    """学生新增 / 编辑表单。"""

    class Meta:
        model = Student
        fields = ["name", "student_no", "gender", "age", "email", "phone", "class_name"]
        labels = {
            "name": "姓名",
            "student_no": "学号",
            "gender": "性别",
            "age": "年龄",
            "email": "邮箱",
            "phone": "电话",
            "class_name": "班级",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "student_no": forms.TextInput(attrs={"class": "form-control"}),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "age": forms.NumberInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "class_name": forms.TextInput(attrs={"class": "form-control"}),
        }


class GradeForm(forms.ModelForm):
    """成绩新增表单（学生字段由视图层通过参数注入，不展示在表单中）。"""

    class Meta:
        model = Grade
        fields = ["subject", "score", "exam_date"]
        labels = {
            "subject": "科目",
            "score": "分数",
            "exam_date": "考试日期",
        }
        widgets = {
            "subject": forms.TextInput(attrs={"class": "form-control"}),
            "score": forms.NumberInput(attrs={"class": "form-control", "step": "0.1"}),
            "exam_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
        }


class StudentSearchForm(forms.Form):
    """学生列表页的搜索 + 性别筛选表单（GET 提交）。"""

    q = forms.CharField(
        label="关键字",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "搜索姓名或学号...",
            }
        ),
    )
    gender = forms.ChoiceField(
        label="性别",
        required=False,
        choices=[("", "全部")] + Student.GENDER_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
