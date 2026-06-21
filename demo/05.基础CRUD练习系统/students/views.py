"""学生成绩管理系统的视图层。

使用基于类的视图 (CBV) 实现学生与成绩的完整 CRUD 操作，
并通过 LoginRequiredMixin 保护写操作。
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import GradeForm, StudentForm, StudentSearchForm
from .models import Grade, Student


class StudentListView(ListView):
    """学生列表视图：支持分页、按姓名/学号搜索、按性别筛选。"""

    model = Student
    template_name = "students/student_list.html"
    context_object_name = "students"
    paginate_by = 10

    def get_queryset(self):
        """根据 GET 参数动态过滤学生列表。"""
        queryset = Student.objects.all()
        q = self.request.GET.get("q", "").strip()
        gender = self.request.GET.get("gender", "").strip()

        if q:
            # 按姓名或学号模糊匹配
            queryset = queryset.filter(
                Q(name__icontains=q) | Q(student_no__icontains=q)
            )
        if gender:
            queryset = queryset.filter(gender=gender)

        return queryset

    def get_context_data(self, **kwargs):
        """将搜索表单与当前参数回填到上下文。"""
        context = super().get_context_data(**kwargs)
        context["search_form"] = StudentSearchForm(self.request.GET or None)
        context["q"] = self.request.GET.get("q", "")
        context["gender"] = self.request.GET.get("gender", "")
        return context


class StudentDetailView(DetailView):
    """学生详情视图：展示学生基本信息与其所有成绩。"""

    model = Student
    template_name = "students/student_detail.html"
    context_object_name = "student"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 关联查询该学生的所有成绩
        context["grades"] = self.object.grades.all().order_by("-created_at")
        # 平均分（无成绩时为 None）
        context["avg_score"] = self.object.grades.aggregate(avg=Avg("score"))["avg"]
        return context


class StudentCreateView(LoginRequiredMixin, CreateView):
    """新建学生视图（需登录）。"""

    model = Student
    form_class = StudentForm
    template_name = "students/student_form.html"
    success_url = reverse_lazy("students:student_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "新建学生"
        context["submit_text"] = "创建"
        return context


class StudentUpdateView(LoginRequiredMixin, UpdateView):
    """编辑学生视图（需登录）。"""

    model = Student
    form_class = StudentForm
    template_name = "students/student_form.html"
    success_url = reverse_lazy("students:student_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "编辑学生"
        context["submit_text"] = "保存"
        return context


class StudentDeleteView(LoginRequiredMixin, DeleteView):
    """删除学生视图（需登录）。"""

    model = Student
    template_name = "students/student_confirm_delete.html"
    context_object_name = "student"
    success_url = reverse_lazy("students:student_list")


class GradeCreateView(LoginRequiredMixin, CreateView):
    """为指定学生添加成绩（需登录）。"""

    model = Grade
    form_class = GradeForm
    template_name = "students/student_form.html"

    def dispatch(self, request, *args, **kwargs):
        """提前获取学生对象，便于在多个方法中复用。"""
        self.student = get_object_or_404(Student, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"为 {self.student.name} 添加成绩"
        context["submit_text"] = "添加"
        context["student_obj"] = self.student
        return context

    def form_valid(self, form):
        """将外键 student 设置为 URL 中的学生对象后再保存。"""
        form.instance.student = self.student
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("students:student_detail", kwargs={"pk": self.student.pk})


def grade_delete(request, pk):
    """删除某条成绩（函数视图，需登录）。"""
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login

        return redirect_to_login(request.get_full_path())

    grade = get_object_or_404(Grade, pk=pk)
    student_pk = grade.student_id

    if request.method == "POST":
        grade.delete()
        return redirect("students:student_detail", pk=student_pk)

    return render(
        request,
        "students/student_confirm_delete.html",
        {
            "student": grade.student,
            "grade": grade,
            "is_grade": True,
        },
    )


def dashboard(request):
    """统计仪表盘：展示学生总数、平均分、科目数、最近添加的学生。"""
    total_students = Student.objects.count()
    avg_score = Grade.objects.aggregate(avg=Avg("score"))["avg"] or 0
    subject_count = Grade.objects.values("subject").distinct().count()
    recent_students = Student.objects.order_by("-created_at")[:5]

    context = {
        "total_students": total_students,
        "avg_score": round(avg_score, 2),
        "subject_count": subject_count,
        "recent_students": recent_students,
    }
    return render(request, "students/dashboard.html", context)
