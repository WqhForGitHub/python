"""Users URL routes."""

from django.urls import path

from . import views

app_name = 'users'

urlpatterns = [
    # 登录 / 注册 / 登出
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),

    # 仪表盘
    path('', views.DashboardView.as_view(), name='dashboard'),

    # 用户管理（员工可见）
    path('list/', views.UserListView.as_view(), name='user_list'),
    path('create/', views.UserCreateView.as_view(), name='user_create'),
    path('<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_edit'),
    path('<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),

    # 个人资料（登录用户）
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path(
        'password/change/',
        views.CustomPasswordChangeView.as_view(),
        name='password_change',
    ),
]
