"""Blog views - 文章列表/详情/发布/编辑/删除 与 评论"""

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import ArticleForm, CommentForm
from .models import Article, Comment


class ArticleListView(ListView):
    """文章列表"""

    model = Article
    template_name = "blog/article_list.html"
    context_object_name = "articles"
    paginate_by = 10


class ArticleDetailView(DetailView):
    """文章详情 + 评论列表 + 评论表单"""

    model = Article
    template_name = "blog/article_detail.html"
    context_object_name = "article"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["comments"] = self.object.comments.all()
        ctx["comment_form"] = CommentForm()
        return ctx


class ArticleCreateView(LoginRequiredMixin, CreateView):
    """发布文章"""

    model = Article
    form_class = ArticleForm
    template_name = "blog/article_form.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class ArticleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """编辑文章（仅作者可编辑）"""

    model = Article
    form_class = ArticleForm
    template_name = "blog/article_form.html"

    def test_func(self):
        article = self.get_object()
        return article.author == self.request.user


class ArticleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """删除文章（仅作者可删除）"""

    model = Article
    template_name = "blog/article_confirm_delete.html"
    success_url = reverse_lazy("blog:article_list")

    def test_func(self):
        article = self.get_object()
        return article.author == self.request.user


@login_required
def add_comment_view(request, pk):
    """提交评论（仅登录用户）"""
    article = get_object_or_404(Article, pk=pk)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.article = article
            comment.author = request.user
            comment.save()
    return redirect("blog:article_detail", pk=article.pk)
