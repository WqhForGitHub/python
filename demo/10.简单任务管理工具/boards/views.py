"""Boards views - 看板、列、卡片视图"""

from django.contrib import messages
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    UserPassesTestMixin,
)
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import BoardForm, CardForm, CardMoveForm, ColumnForm
from .models import Board, Card, Column


class BoardAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """看板访问权限：所有者或成员（或超级用户）可访问。

    用于 DetailView / UpdateView 等通过 get_object 获取看板的视图。
    """

    def test_func(self):
        board = self.get_object()
        user = self.request.user
        if user.is_superuser:
            return True
        if board.owner == user:
            return True
        if user in board.members.all():
            return True
        return False


class BoardListView(LoginRequiredMixin, ListView):
    """看板列表：展示当前用户拥有的看板与被共享的看板。"""

    model = Board
    template_name = 'boards/board_list.html'
    context_object_name = 'boards'
    paginate_by = 12

    def get_queryset(self):
        user = self.request.user
        # 用户拥有的看板 + 被共享的看板（去重）
        owned = Board.objects.filter(owner=user)
        shared = Board.objects.filter(members=user)
        return (owned | shared).distinct()


class BoardDetailView(BoardAccessMixin, DetailView):
    """看板详情：展示看板的列与卡片（Kanban 视图）。"""

    model = Board
    template_name = 'boards/board_detail.html'
    context_object_name = 'board'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        board = self.get_object()
        columns = board.columns.all()
        # 为每列准备卡片与表单
        columns_with_cards = []
        for column in columns:
            columns_with_cards.append({
                'column': column,
                'cards': column.cards.all(),
                'card_form': CardForm(),
                'move_form': CardMoveForm(board=board),
            })
        context['columns_with_cards'] = columns_with_cards
        context['column_form'] = ColumnForm()
        context['board_members'] = board.members.all()
        return context


class BoardCreateView(LoginRequiredMixin, CreateView):
    """看板创建：自动设置所有者为当前用户。"""

    model = Board
    form_class = BoardForm
    template_name = 'boards/board_form.html'
    success_url = reverse_lazy('boards:board_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, '看板已创建。')
        return super().form_valid(form)


class BoardUpdateView(BoardAccessMixin, UpdateView):
    """看板编辑：所有者或成员可访问。"""

    model = Board
    form_class = BoardForm
    template_name = 'boards/board_form.html'

    def form_valid(self, form):
        messages.success(self.request, '看板已更新。')
        return super().form_valid(form)

    def get_success_url(self):
        # 重定向回看板详情页
        from django.urls import reverse
        return reverse('boards:board_detail', kwargs={'pk': self.object.pk})


class BoardDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """看板删除：仅所有者可删除。"""

    model = Board
    template_name = 'boards/board_confirm_delete.html'
    success_url = reverse_lazy('boards:board_list')

    def test_func(self):
        board = self.get_object()
        user = self.request.user
        if user.is_superuser:
            return True
        return board.owner == user

    def form_valid(self, form):
        messages.success(self.request, '看板已删除。')
        return super().form_valid(form)


def _user_can_access_board(user, board):
    """判断用户是否能访问某看板（所有者 / 成员 / 超级用户）。"""
    if user.is_superuser:
        return True
    if board.owner == user:
        return True
    return user in board.members.all()


def column_create(request, pk):
    """在看板中添加列。所有者或成员可操作。"""
    board = get_object_or_404(Board, pk=pk)
    if not _user_can_access_board(request.user, board):
        return HttpResponseForbidden('无权操作该看板。')
    if request.method == 'POST':
        form = ColumnForm(request.POST)
        if form.is_valid():
            column = form.save(commit=False)
            column.board = board
            # 新列默认排到末尾
            last_order = board.columns.count()
            column.order = last_order
            column.save()
            messages.success(request, f'列表「{column.title}」已添加。')
        else:
            messages.error(request, '列表添加失败，请检查输入。')
    return redirect('boards:board_detail', pk=board.pk)


def card_create(request, pk):
    """在列中添加卡片。"""
    column = get_object_or_404(Column, pk=pk)
    board = column.board
    if not _user_can_access_board(request.user, board):
        return HttpResponseForbidden('无权操作该看板。')
    if request.method == 'POST':
        form = CardForm(request.POST)
        if form.is_valid():
            card = form.save(commit=False)
            card.column = column
            # 新卡片默认排到列末尾
            last_order = column.cards.count()
            card.order = last_order
            card.save()
            messages.success(request, f'卡片「{card.title}」已添加。')
        else:
            messages.error(request, '卡片添加失败，请检查输入。')
    return redirect('boards:board_detail', pk=board.pk)


def card_edit(request, pk):
    """编辑卡片：看板所有者或卡片负责人可操作。"""
    card = get_object_or_404(Card, pk=pk)
    board = card.column.board
    user = request.user
    if not (
        user.is_superuser
        or board.owner == user
        or card.assignee == user
    ):
        return HttpResponseForbidden('无权编辑该卡片。')
    if request.method == 'POST':
        form = CardForm(request.POST, instance=card)
        if form.is_valid():
            form.save()
            messages.success(request, '卡片已更新。')
        else:
            messages.error(request, '卡片更新失败，请检查输入。')
    return redirect('boards:board_detail', pk=board.pk)


def card_delete(request, pk):
    """删除卡片：所有者或负责人可操作。"""
    card = get_object_or_404(Card, pk=pk)
    board = card.column.board
    user = request.user
    if not (
        user.is_superuser
        or board.owner == user
        or card.assignee == user
    ):
        return HttpResponseForbidden('无权删除该卡片。')
    if request.method == 'POST':
        card.delete()
        messages.success(request, '卡片已删除。')
    return redirect('boards:board_detail', pk=board.pk)


def card_move(request, pk):
    """移动卡片到目标列并设置顺序。

    通过表单 POST 提交 target_column_id 与 new_order。
    为保持简单：将目标列中顺序 >= new_order 的其他卡片后移一位。
    """
    card = get_object_or_404(Card, pk=pk)
    board = card.column.board
    if not _user_can_access_board(request.user, board):
        return HttpResponseForbidden('无权操作该看板。')
    if request.method == 'POST':
        target_column_id = request.POST.get('target_column_id')
        new_order = request.POST.get('new_order', '0')
        try:
            target_column = Column.objects.get(pk=target_column_id, board=board)
        except (Column.DoesNotExist, ValueError):
            messages.error(request, '目标列表不存在。')
            return redirect('boards:board_detail', pk=board.pk)
        try:
            new_order_int = int(new_order)
        except ValueError:
            new_order_int = 0

        old_column = card.column
        # 将卡片移到目标列
        card.column = target_column
        card.order = new_order_int
        # 把目标列中顺序 >= new_order 的其它卡片后移一位（排除当前卡片）
        siblings = target_column.cards.exclude(pk=card.pk).filter(
            order__gte=new_order_int,
        )
        for sibling in siblings:
            sibling.order += 1
            sibling.save()
        card.save()
        messages.success(request, f'卡片已移动到「{target_column.title}」。')
    return redirect('boards:board_detail', pk=board.pk)
