"""
项目应用 - 视图。

包含项目与任务的增删改查（CBV），并通过 ManagerRequiredMixin
对写操作进行角色控制。任务状态快速切换由函数视图完成。
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import ProjectForm, ProjectSearchForm, TaskForm
from .models import Project, Task


class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """部门经理/管理员/超级用户混入类。"""

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (
            user.is_manager or user.is_admin or user.is_superuser
        )

    def handle_no_permission(self):
        from django.contrib import messages

        messages.error(self.request, "您没有执行此操作的权限。")
        return super().handle_no_permission()


# =============== 项目视图 ===============


class ProjectListView(LoginRequiredMixin, ListView):
    """项目列表（搜索/过滤）。"""

    model = Project
    template_name = "projects/project_list.html"
    context_object_name = "projects"
    paginate_by = 20

    def get_queryset(self):
        qs = Project.objects.select_related("manager", "department")
        form = ProjectSearchForm(self.request.GET)
        if form.is_valid():
            q = form.cleaned_data.get("q")
            if q:
                qs = qs.filter(Q(name__icontains=q) | Q(code__icontains=q))
            status = form.cleaned_data.get("status")
            if status:
                qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["search_form"] = ProjectSearchForm(self.request.GET or None)
        return ctx


class ProjectDetailView(LoginRequiredMixin, DetailView):
    """项目详情。"""

    model = Project
    template_name = "projects/project_detail.html"
    context_object_name = "project"

    def get_queryset(self):
        return Project.objects.select_related("manager", "department").prefetch_related(
            "members", "tasks"
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["tasks"] = self.object.tasks.select_related("assignee").all()
        ctx["members"] = self.object.members.all()
        return ctx


class ProjectCreateView(ManagerRequiredMixin, SuccessMessageMixin, CreateView):
    """新增项目。"""

    model = Project
    form_class = ProjectForm
    template_name = "projects/project_form.html"
    success_url = reverse_lazy("projects:project_list")
    success_message = "项目「%(name)s」已创建。"


class ProjectUpdateView(ManagerRequiredMixin, SuccessMessageMixin, UpdateView):
    """编辑项目。"""

    model = Project
    form_class = ProjectForm
    template_name = "projects/project_form.html"
    success_url = reverse_lazy("projects:project_list")
    success_message = "项目「%(name)s」已更新。"


class ProjectDeleteView(ManagerRequiredMixin, DeleteView):
    """删除项目。"""

    model = Project
    template_name = "projects/project_confirm_delete.html"
    context_object_name = "project"
    success_url = reverse_lazy("projects:project_list")

    def form_valid(self, form):
        from django.contrib import messages

        messages.success(self.request, f"项目「{self.object.name}」已删除。")
        return super().form_valid(form)


# =============== 任务视图 ===============


class TaskListView(LoginRequiredMixin, ListView):
    """任务列表（按项目/状态过滤）。"""

    model = Task
    template_name = "projects/task_list.html"
    context_object_name = "tasks"
    paginate_by = 20

    def get_queryset(self):
        qs = Task.objects.select_related("project", "assignee")
        project_id = self.request.GET.get("project")
        if project_id:
            qs = qs.filter(project_id=project_id)
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["projects"] = Project.objects.all()
        ctx["status_choices"] = Task.STATUS_CHOICES
        ctx["current_project"] = self.request.GET.get("project", "")
        ctx["current_status"] = self.request.GET.get("status", "")
        return ctx


class TaskCreateView(ManagerRequiredMixin, SuccessMessageMixin, CreateView):
    """新增任务。"""

    model = Task
    form_class = TaskForm
    template_name = "projects/task_form.html"
    success_url = reverse_lazy("projects:task_list")
    success_message = "任务「%(title)s」已创建。"

    def get_initial(self):
        initial = super().get_initial()
        project_id = self.request.GET.get("project")
        if project_id:
            initial["project"] = project_id
        return initial


class TaskUpdateView(ManagerRequiredMixin, SuccessMessageMixin, UpdateView):
    """编辑任务。"""

    model = Task
    form_class = TaskForm
    template_name = "projects/task_form.html"
    success_url = reverse_lazy("projects:task_list")
    success_message = "任务「%(title)s」已更新。"


class TaskDeleteView(ManagerRequiredMixin, DeleteView):
    """删除任务。"""

    model = Task
    template_name = "projects/task_confirm_delete.html"
    context_object_name = "task"
    success_url = reverse_lazy("projects:task_list")

    def form_valid(self, form):
        from django.contrib import messages

        messages.success(self.request, f"任务「{self.object.title}」已删除。")
        return super().form_valid(form)


def task_toggle_status(request, pk):
    """快速切换任务状态（待办 <-> 已完成）。

    任何登录用户均可切换（便于演示），完成后跳回来源页。
    """
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    task = get_object_or_404(Task, pk=pk)
    if task.status == Task.STATUS_DONE:
        task.status = Task.STATUS_TODO
        task.completed_at = None
    else:
        task.status = Task.STATUS_DONE
        task.completed_at = timezone.now()
    task.save()
    from django.contrib import messages

    messages.success(request, f"任务「{task.title}」状态已更新。")
    # 返回来源页或任务列表
    next_url = request.GET.get("next") or request.POST.get("next")
    if next_url:
        return redirect(next_url)
    return redirect("projects:task_list")
