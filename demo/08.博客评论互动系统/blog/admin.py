"""
博客后台管理注册。
"""
from django.contrib import admin

from .models import Tag, Post, Comment, Like


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """标签管理。"""
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """文章管理。"""
    list_display = ('title', 'author', 'views', 'is_published', 'created_at')
    list_filter = ('is_published', 'created_at', 'tags')
    search_fields = ('title', 'content', 'excerpt')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('tags',)
    raw_id_fields = ('author',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """评论管理。"""
    list_display = ('author', 'post', 'parent', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('content', 'author__username', 'post__title')
    raw_id_fields = ('post', 'author', 'parent')
    ordering = ('-created_at',)


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    """点赞管理。"""
    list_display = ('user', 'post', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'post__title')
    raw_id_fields = ('post', 'user')
    ordering = ('-created_at',)
