"""Blog admin - 文章与评论的后台管理"""

from django.contrib import admin

from .models import Article, Comment


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at', 'updated_at')
    list_filter = ('created_at', 'author')
    search_fields = ('title', 'body')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'article', 'created_at')
    list_filter = ('created_at', 'author')
    search_fields = ('body',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
