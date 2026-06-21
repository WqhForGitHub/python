"""
仪表盘应用 - 视图。

聚合员工、部门、项目、任务的统计数据，并渲染首页仪表盘。
"""
from collections import OrderedDict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.views.generic import TemplateView

from accounts.models import User
from employees.models import Department, Employee
from projects.models import Project, Task


class DashboardIndexView(LoginRequiredMixin, TemplateView):
    """首页仪表盘视图。"""

    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # ---- 概览统计 ----
        ctx['total_employees'] = Employee.objects.count()
        ctx['total_users'] = User.objects.count()
        ctx['total_departments'] = Department.objects.count()
        ctx['total_projects'] = Project.objects.count()
        ctx['total_tasks'] = Task.objects.count()

        # 进行中项目数
        ctx['in_progress_projects'] = Project.objects.filter(
            status=Project.STATUS_IN_PROGRESS
        ).count()
        # 待办任务数
        ctx['todo_tasks'] = Task.objects.filter(status=Task.STATUS_TODO).count()
        ctx['doing_tasks'] = Task.objects.filter(status=Task.STATUS_DOING).count()
        ctx['done_tasks'] = Task.objects.filter(status=Task.STATUS_DONE).count()

        # ---- 项目状态分布 ----
        project_status_qs = Project.objects.values('status').annotate(
            count=Count('pk')
        ).order_by('status')
        status_map = dict(Project.STATUS_CHOICES)
        ctx['project_status_breakdown'] = [
            {
                'status': status_map.get(item['status'], item['status']),
                'code': item['status'],
                'count': item['count'],
            }
            for item in project_status_qs
        ]

        # ---- 任务状态分布 ----
        task_status_qs = Task.objects.values('status').annotate(
            count=Count('pk')
        ).order_by('status')
        task_status_map = dict(Task.STATUS_CHOICES)
        ctx['task_status_breakdown'] = [
            {
                'status': task_status_map.get(item['status'], item['status']),
                'code': item['status'],
                'count': item['count'],
            }
            for item in task_status_qs
        ]

        # ---- 部门人员分布 ----
        dept_headcount = Department.objects.annotate(
            member_count=Count('members', distinct=True),
            employee_count=Count('employees', distinct=True),
        ).order_by('-member_count', 'name')
        ctx['department_headcount'] = list(dept_headcount)
        # 最大值用于绘制进度条
        ctx['max_dept_count'] = max(
            [d.member_count for d in dept_headcount] + [1]
        )

        # ---- 最近项目 ----
        ctx['recent_projects'] = Project.objects.select_related(
            'manager', 'department'
        ).order_by('-created_at')[:5]

        # ---- 最近员工 ----
        ctx['recent_employees'] = Employee.objects.select_related(
            'user', 'department'
        ).order_by('-created_at')[:5]

        # ---- 最近任务 ----
        ctx['recent_tasks'] = Task.objects.select_related(
            'project', 'assignee'
        ).order_by('-created_at')[:5]

        return ctx


index = DashboardIndexView.as_view()
