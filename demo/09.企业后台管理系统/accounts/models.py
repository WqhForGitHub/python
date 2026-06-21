"""
账户应用 - 用户模型。

自定义用户模型扩展自 AbstractUser，增加员工编号、部门、角色、
电话、头像、入职日期等企业相关字段。
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """企业用户模型。"""

    # 角色选择
    ROLE_STAFF = 'staff'
    ROLE_MANAGER = 'manager'
    ROLE_ADMIN = 'admin'
    ROLE_CHOICES = [
        (ROLE_STAFF, '普通员工'),
        (ROLE_MANAGER, '部门经理'),
        (ROLE_ADMIN, '管理员'),
    ]

    # 员工编号
    employee_no = models.CharField(
        '员工编号', max_length=30, unique=True, blank=True,
        help_text='员工唯一编号，可留空'
    )

    # 所属部门（与 employees.Department 形成循环依赖，故使用字符串引用）
    department = models.ForeignKey(
        'employees.Department', verbose_name='所属部门',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='members'
    )

    # 角色
    role = models.CharField(
        '角色', max_length=20, choices=ROLE_CHOICES, default=ROLE_STAFF
    )

    # 电话
    phone = models.CharField('联系电话', max_length=20, blank=True)

    # 头像
    avatar = models.ImageField(
        '头像', upload_to='avatars/', blank=True, null=True
    )

    # 入职日期
    hire_date = models.DateField('入职日期', null=True, blank=True)

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'
        ordering = ['date_joined']

    def __str__(self):
        return self.get_full_name() or self.username

    # ---- 角色判定属性 ----
    @property
    def is_manager(self):
        """是否为部门经理。"""
        return self.role == self.ROLE_MANAGER

    @property
    def is_admin(self):
        """是否为管理员（不含超级用户）。"""
        return self.role == self.ROLE_ADMIN

    @property
    def is_staff_role(self):
        """是否为普通员工。"""
        return self.role == self.ROLE_STAFF

    @property
    def display_name(self):
        """显示名称：真实姓名优先，其次用户名。"""
        full = self.get_full_name()
        return full if full else self.username
