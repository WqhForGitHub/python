"""Users views - 用户管理系统的核心视图

包含：
- 注册 / 登录 / 登出
- 个人资料查看 / 编辑 / 修改密码
- 用户列表 / 详情 / 新建 / 编辑 / 删除（仅员工可访问）
- 仪表盘（员工可见，统计用户数据）
"""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import (
    LoginView as AuthLoginView,
    LogoutView as AuthLogoutView,
    PasswordChangeView as AuthPasswordChangeView,
)
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import timedelta
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import (
    LoginForm,
    ProfileForm,
    UserAdminForm,
    UserRegisterForm,
    CustomPasswordChangeForm,
)
from .models import User


# ---------------------------------------------------------------------
# 注册 / 登录 / 登出
# ---------------------------------------------------------------------

def register_view(request):
    """用户注册"""
    if request.user.is_authenticated:
        return redirect('users:dashboard')
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '注册成功，欢迎加入！')
            return redirect('users:dashboard')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})


class CustomLoginView(AuthLoginView):
    """登录视图 - 使用自定义 LoginForm"""

    form_class = LoginForm
    template_name = 'registration/login.html'
    redirect_authenticated_user = True


class CustomLogoutView(AuthLogoutView):
    """登出视图"""
    next_page = 'login'


# ---------------------------------------------------------------------
# 仪表盘（员工可见）
# ---------------------------------------------------------------------

class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """员工权限混入：仅 is_staff=True 的用户可访问"""

    def test_func(self):
        return self.request.user.is_staff


class DashboardView(StaffRequiredMixin, TemplateView):
    """仪表盘：展示用户统计信息"""

    template_name = 'users/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()
        seven_days_ago = now - timedelta(days=7)
        thirty_days_ago = now - timedelta(days=30)

        ctx['total_users'] = User.objects.count()
        ctx['active_users'] = User.objects.filter(is_active=True).count()
        ctx['disabled_users'] = ctx['total_users'] - ctx['active_users']
        ctx['staff_users'] = User.objects.filter(is_staff=True).count()
        ctx['superusers'] = User.objects.filter(is_superuser=True).count()
        ctx['new_users_7d'] = User.objects.filter(
            date_joined__gte=seven_days_ago,
        ).count()
        ctx['new_users_30d'] = User.objects.filter(
            date_joined__gte=thirty_days_ago,
        ).count()
        # 最近 7 天每日注册数（用于前端图表展示）
        recent = (
            User.objects.filter(date_joined__gte=seven_days_ago)
            .extra({'day': "date(date_joined)"})
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )
        ctx['recent_daily'] = list(recent)
        ctx['latest_users'] = User.objects.order_by('-date_joined')[:5]
        return ctx


# ---------------------------------------------------------------------
# 用户列表 / 详情 / 增删改（员工可见）
# ---------------------------------------------------------------------

class UserListView(StaffRequiredMixin, ListView):
    """用户列表：支持搜索与分页"""

    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(username__icontains=q)
                | Q(email__icontains=q)
                | Q(phone__icontains=q),
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['query'] = self.request.GET.get('q', '')
        return ctx


class UserDetailView(StaffRequiredMixin, DetailView):
    """用户详情"""

    model = User
    template_name = 'users/user_detail.html'
    context_object_name = 'user_obj'


class UserCreateView(StaffRequiredMixin, CreateView):
    """管理员新建用户"""

    model = User
    form_class = UserAdminForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('users:user_list')

    def form_valid(self, form):
        messages.success(self.request, f'用户 {form.instance.username} 创建成功')
        return super().form_valid(form)


class UserUpdateView(StaffRequiredMixin, UpdateView):
    """管理员编辑用户"""

    model = User
    form_class = UserAdminForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('users:user_list')

    def form_valid(self, form):
        messages.success(self.request, f'用户 {form.instance.username} 更新成功')
        return super().form_valid(form)


class UserDeleteView(StaffRequiredMixin, DeleteView):
    """管理员删除用户（不可删除自己）"""

    model = User
    template_name = 'users/user_confirm_delete.html'
    context_object_name = 'user_obj'
    success_url = reverse_lazy('users:user_list')

    def test_func(self):
        # 不可删除自己
        target = self.get_object()
        return self.request.user.is_staff and target != self.request.user

    def form_valid(self, form):
        messages.success(self.request, '用户删除成功')
        return super().form_valid(form)


# ---------------------------------------------------------------------
# 个人资料（登录用户）
# ---------------------------------------------------------------------

class ProfileView(LoginRequiredMixin, DetailView):
    """查看个人资料"""

    template_name = 'users/profile.html'
    context_object_name = 'user_obj'

    def get_object(self, queryset=None):
        return self.request.user


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """编辑个人资料"""

    form_class = ProfileForm
    template_name = 'users/profile_edit.html'
    success_url = reverse_lazy('users:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, '个人资料更新成功')
        return super().form_valid(form)


class CustomPasswordChangeView(LoginRequiredMixin, AuthPasswordChangeView):
    """修改密码"""

    form_class = CustomPasswordChangeForm
    template_name = 'users/password_change.html'
    success_url = reverse_lazy('users:profile')

    def form_valid(self, form):
        messages.success(self.request, '密码修改成功')
        return super().form_valid(form)
