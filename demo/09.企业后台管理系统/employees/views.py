"""
员工应用 - 视图。

包含部门与员工的增删改查（CBV），并通过 ManagerRequiredMixin
对写操作进行角色控制。
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)

from .forms import DepartmentForm, EmployeeForm, EmployeeSearchForm
from .models import Department, Employee


class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """部门经理/管理员/超级用户混入类。

    只有 manager、admin 角色或超级用户才能通过权限校验。
    """

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (
            user.is_manager or user.is_admin or user.is_superuser
        )

    def handle_no_permission(self):
        from django.contrib import messages
        messages.error(self.request, '您没有执行此操作的权限。')
        return super().handle_no_permission()


# =============== 部门视图 ===============

class DepartmentListView(LoginRequiredMixin, ListView):
    """部门列表。"""

    model = Department
    template_name = 'employees/department_list.html'
    context_object_name = 'departments'
    paginate_by = 20

    def get_queryset(self):
        qs = Department.objects.select_related('manager', 'parent')
        return qs


class DepartmentDetailView(LoginRequiredMixin, DetailView):
    """部门详情。"""

    model = Department
    template_name = 'employees/department_detail.html'
    context_object_name = 'department'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['members'] = self.object.members.select_related('department').all()
        ctx['employees'] = self.object.employees.select_related('user').all()
        ctx['children'] = self.object.children.all()
        return ctx


class DepartmentCreateView(ManagerRequiredMixin, SuccessMessageMixin, CreateView):
    """新增部门。"""

    model = Department
    form_class = DepartmentForm
    template_name = 'employees/department_form.html'
    success_url = reverse_lazy('employees:department_list')
    success_message = '部门「%(name)s」已创建。'


class DepartmentUpdateView(ManagerRequiredMixin, SuccessMessageMixin, UpdateView):
    """编辑部门。"""

    model = Department
    form_class = DepartmentForm
    template_name = 'employees/department_form.html'
    success_url = reverse_lazy('employees:department_list')
    success_message = '部门「%(name)s」已更新。'


class DepartmentDeleteView(ManagerRequiredMixin, DeleteView):
    """删除部门。"""

    model = Department
    template_name = 'employees/department_confirm_delete.html'
    context_object_name = 'department'
    success_url = reverse_lazy('employees:department_list')

    def form_valid(self, form):
        from django.contrib import messages
        messages.success(self.request, f'部门「{self.object.name}」已删除。')
        return super().form_valid(form)


# =============== 员工视图 ===============

class EmployeeListView(LoginRequiredMixin, ListView):
    """员工列表（支持搜索/过滤）。"""

    model = Employee
    template_name = 'employees/employee_list.html'
    context_object_name = 'employees'
    paginate_by = 20

    def get_queryset(self):
        qs = Employee.objects.select_related('user', 'department')
        form = EmployeeSearchForm(self.request.GET)
        if form.is_valid():
            q = form.cleaned_data.get('q')
            if q:
                qs = qs.filter(
                    Q(user__username__icontains=q)
                    | Q(position__icontains=q)
                    | Q(user__first_name__icontains=q)
                    | Q(user__last_name__icontains=q)
                )
            department = form.cleaned_data.get('department')
            if department:
                qs = qs.filter(department=department)
            status = form.cleaned_data.get('status')
            if status:
                qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['search_form'] = EmployeeSearchForm(self.request.GET or None)
        return ctx


class EmployeeDetailView(LoginRequiredMixin, DetailView):
    """员工详情。"""

    model = Employee
    template_name = 'employees/employee_detail.html'
    context_object_name = 'employee'

    def get_queryset(self):
        return Employee.objects.select_related('user', 'department')


class EmployeeCreateView(ManagerRequiredMixin, SuccessMessageMixin, CreateView):
    """新增员工。"""

    model = Employee
    form_class = EmployeeForm
    template_name = 'employees/employee_form.html'
    success_url = reverse_lazy('employees:employee_list')
    success_message = '员工「%(user)s」已创建。'


class EmployeeUpdateView(ManagerRequiredMixin, SuccessMessageMixin, UpdateView):
    """编辑员工。"""

    model = Employee
    form_class = EmployeeForm
    template_name = 'employees/employee_form.html'
    success_url = reverse_lazy('employees:employee_list')
    success_message = '员工「%(user)s」已更新。'


class EmployeeDeleteView(ManagerRequiredMixin, DeleteView):
    """删除员工。"""

    model = Employee
    template_name = 'employees/employee_confirm_delete.html'
    context_object_name = 'employee'
    success_url = reverse_lazy('employees:employee_list')

    def form_valid(self, form):
        from django.contrib import messages
        messages.success(self.request, f'员工「{self.object.user.username}」已删除。')
        return super().form_valid(form)
