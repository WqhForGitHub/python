"""
博客视图：文章列表/详情/增删改、评论、点赞、标签筛选。
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView

from .forms import PostForm, CommentForm, SearchForm
from .models import Post, Comment, Like, Tag


def post_list(request):
    """文章列表：支持标签筛选、关键词搜索、分页。"""
    posts = Post.objects.filter(is_published=True)

    # 标签筛选
    tag_slug = request.GET.get('tag')
    current_tag = None
    if tag_slug:
        current_tag = get_object_or_404(Tag, name=tag_slug)
        posts = posts.filter(tags=current_tag)

    # 关键词搜索（标题或正文）
    query = request.GET.get('q', '').strip()
    if query:
        posts = posts.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        )

    # 分页：每页 10 篇
    from django.core.paginator import Paginator
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 标签云：所有标签
    all_tags = Tag.objects.all()

    # 搜索表单
    search_form = SearchForm(initial={'q': query})

    context = {
        'page_obj': page_obj,
        'all_tags': all_tags,
        'current_tag': current_tag,
        'query': query,
        'search_form': search_form,
    }
    return render(request, 'blog/post_list.html', context)


def posts_by_tag(request, slug):
    """按标签 slug 筛选文章。"""
    tag = get_object_or_404(Tag, name=slug)
    posts = Post.objects.filter(is_published=True, tags=tag)

    from django.core.paginator import Paginator
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'all_tags': Tag.objects.all(),
        'current_tag': tag,
        'query': '',
        'search_form': SearchForm(),
    }
    return render(request, 'blog/post_list.html', context)


def post_detail(request, slug):
    """文章详情：累加浏览量、展示评论树、点赞计数。"""
    post = get_object_or_404(Post, slug=slug, is_published=True)

    # 累加浏览量（使用 F 表达式避免并发问题）
    from django.db.models import F
    Post.objects.filter(pk=post.pk).update(views=F('views') + 1)
    post.refresh_from_db()

    # 顶层评论（无父评论）
    comments = post.comments.filter(is_active=True, parent__isnull=True)

    # 所有评论数（含回复）
    comment_count = post.comments.filter(is_active=True).count()

    # 点赞数 & 当前用户是否已点赞
    like_count = post.likes.count()
    user_liked = False
    if request.user.is_authenticated:
        user_liked = post.likes.filter(user=request.user).exists()

    # 评论表单
    comment_form = CommentForm()

    context = {
        'post': post,
        'comments': comments,
        'comment_count': comment_count,
        'like_count': like_count,
        'user_liked': user_liked,
        'comment_form': comment_form,
    }
    return render(request, 'blog/post_detail.html', context)


class PostCreateView(LoginRequiredMixin, CreateView):
    """发表文章。"""
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'
    success_url = reverse_lazy('blog:post_list')

    def form_valid(self, form):
        # 设置作者为当前登录用户
        form.instance.author = self.request.user
        messages.success(self.request, '文章发表成功！')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_create'] = True
        return context


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """编辑文章（仅作者本人）。"""
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'

    def test_func(self):
        # 仅作者本人可编辑
        post = self.get_object()
        return post.author == self.request.user

    def handle_no_permission(self):
        messages.error(self.request, '你无权编辑此文章。')
        return redirect('blog:post_detail', slug=self.get_object().slug)

    def form_valid(self, form):
        messages.success(self.request, '文章已更新。')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_create'] = False
        return context


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """删除文章（仅作者本人）。"""
    model = Post
    template_name = 'blog/post_confirm_delete.html'
    success_url = reverse_lazy('blog:post_list')

    def test_func(self):
        # 仅作者本人可删除
        post = self.get_object()
        return post.author == self.request.user

    def handle_no_permission(self):
        messages.error(self.request, '你无权删除此文章。')
        return redirect('blog:post_detail', slug=self.get_object().slug)

    def form_valid(self, form):
        messages.success(self.request, '文章已删除。')
        return super().form_valid(form)


from django.contrib.auth.decorators import login_required


@login_required
def comment_create(request, slug):
    """对文章发表评论或回复（支持 parent_id）。"""
    post = get_object_or_404(Post, slug=slug, is_published=True)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user

            # 处理回复
            parent_id = request.POST.get('parent_id')
            if parent_id:
                try:
                    parent_comment = Comment.objects.get(pk=parent_id, post=post)
                    comment.parent = parent_comment
                except Comment.DoesNotExist:
                    pass

            comment.save()
            messages.success(request, '评论发表成功！')
        else:
            messages.error(request, '评论内容不能为空。')
    return redirect('blog:post_detail', slug=slug)


@login_required
def like_toggle(request, slug):
    """点赞 / 取消点赞。支持 JSON 与重定向两种响应。"""
    post = get_object_or_404(Post, slug=slug, is_published=True)

    if request.method == 'POST':
        like, created = Like.objects.get_or_create(post=post, user=request.user)
        if not created:
            # 已存在则取消点赞
            like.delete()
            liked = False
        else:
            liked = True
        like_count = post.likes.count()

        # 若是 AJAX 请求返回 JSON
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'liked': liked,
                'like_count': like_count,
            })
        messages.success(request, '已点赞' if liked else '已取消点赞')
        return redirect('blog:post_detail', slug=slug)

    # 非 POST 请求直接跳回详情
    return redirect('blog:post_detail', slug=slug)
