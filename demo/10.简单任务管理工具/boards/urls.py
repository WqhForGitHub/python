"""Boards urls - 看板应用路由"""

from django.urls import path

from . import views

app_name = 'boards'

urlpatterns = [
    # 看板列表（首页）
    path('', views.BoardListView.as_view(), name='board_list'),
    # 看板创建
    path('boards/new/', views.BoardCreateView.as_view(), name='board_create'),
    # 看板详情（Kanban 视图）
    path('boards/<int:pk>/', views.BoardDetailView.as_view(), name='board_detail'),
    # 看板编辑
    path(
        'boards/<int:pk>/edit/',
        views.BoardUpdateView.as_view(),
        name='board_edit',
    ),
    # 看板删除
    path(
        'boards/<int:pk>/delete/',
        views.BoardDeleteView.as_view(),
        name='board_delete',
    ),
    # 在看板中添加列
    path(
        'boards/<int:pk>/columns/new/',
        views.column_create,
        name='column_create',
    ),
    # 在列中添加卡片
    path(
        'columns/<int:pk>/cards/new/',
        views.card_create,
        name='card_create',
    ),
    # 编辑卡片
    path('cards/<int:pk>/edit/', views.card_edit, name='card_edit'),
    # 删除卡片
    path('cards/<int:pk>/delete/', views.card_delete, name='card_delete'),
    # 移动卡片
    path('cards/<int:pk>/move/', views.card_move, name='card_move'),
]
