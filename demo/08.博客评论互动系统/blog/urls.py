"""
blog 应用 URL 路由，命名空间 'blog'。
"""
from django.urls import path

from . import views

app_name = 'blog'

urlpatterns = [
    # 文章列表
    path('', views.post_list, name='post_list'),
    # 发表文章
    path('post/new/', views.PostCreateView.as_view(), name='post_create'),
    # 文章详情
    path('post/<slug:slug>/', views.post_detail, name='post_detail'),
    # 编辑文章
    path('post/<slug:slug>/edit/', views.PostUpdateView.as_view(), name='post_edit'),
    # 删除文章
    path('post/<slug:slug>/delete/', views.PostDeleteView.as_view(), name='post_delete'),
    # 发表评论
    path('post/<slug:slug>/comment/', views.comment_create, name='comment_create'),
    # 点赞切换
    path('post/<slug:slug>/like/', views.like_toggle, name='like_toggle'),
    # 按标签筛选
    path('tag/<slug:slug>/', views.posts_by_tag, name='posts_by_tag'),
]
