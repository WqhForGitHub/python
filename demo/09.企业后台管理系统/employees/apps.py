"""employees 应用配置。"""

from django.apps import AppConfig


class EmployeesConfig(AppConfig):
    """员工与部门应用配置。"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "employees"
    verbose_name = "员工管理"
