"""
员工应用 - URL 路由。

命名空间：employees
"""
from django.urls import path

from . import views

app_name = 'employees'

urlpatterns = [
    # 部门管理
    path('departments/', views.DepartmentListView.as_view(), name='department_list'),
    path('departments/new/', views.DepartmentCreateView.as_view(), name='department_create'),
    path('departments/<int:pk>/', views.DepartmentDetailView.as_view(), name='department_detail'),
    path('departments/<int:pk>/edit/', views.DepartmentUpdateView.as_view(), name='department_edit'),
    path('departments/<int:pk>/delete/', views.DepartmentDeleteView.as_view(), name='department_delete'),
    # 员工管理
    path('', views.EmployeeListView.as_view(), name='employee_list'),
    path('new/', views.EmployeeCreateView.as_view(), name='employee_create'),
    path('<int:pk>/', views.EmployeeDetailView.as_view(), name='employee_detail'),
    path('<int:pk>/edit/', views.EmployeeUpdateView.as_view(), name='employee_edit'),
    path('<int:pk>/delete/', views.EmployeeDeleteView.as_view(), name='employee_delete'),
]
