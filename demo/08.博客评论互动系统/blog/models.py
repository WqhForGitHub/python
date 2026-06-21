"""
博客数据模型：标签、文章、评论、点赞。
"""
from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Tag(models.Model):
    """文章标签。"""

    name = models.CharField('标签名', max_length=30, unique=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '标签'
        verbose_name_plural = '标签'
        ordering = ['name']

    def __str__(self):
        return self.name


class Post(models.Model):
    """博客文章。"""

    title = models.CharField('标题', max_length=200)
    # slug 自动从标题生成，允许创建时为空
    slug = models.SlugField('slug', unique=True, blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='作者',
    )
    excerpt = models.CharField('摘要', max_length=300, blank=True)
    content = models.TextField('正文')
    cover = models.ImageField('封面图', upload_to='post_covers/', blank=True, null=True)
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='posts',
        verbose_name='标签',
    )
    views = models.IntegerField('浏览量', default=0)
    is_published = models.BooleanField('已发布', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '文章'
        verbose_name_plural = '文章'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # 若未指定 slug，则根据标题自动生成；若冲突则附加主键
        if not self.slug:
            base_slug = slugify(self.title)
            # slugify 对纯中文可能返回空字符串，做兜底处理
            slug = base_slug or 'post'
            # 确保唯一性
            candidate = slug
            counter = 1
            qs = Post.objects.filter(slug=candidate)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            while qs.exists():
                candidate = f'{slug}-{counter}'
                counter += 1
                qs = Post.objects.filter(slug=candidate)
                if self.pk:
                    qs = qs.exclude(pk=self.pk)
            self.slug = candidate
        super().save(*args, **kwargs)


class Comment(models.Model):
    """文章评论，支持嵌套回复。"""

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='文章',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='评论者',
    )
    # 自引用外键，实现评论的回复
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies',
        verbose_name='父评论',
    )
    content = models.TextField('评论内容')
    is_active = models.BooleanField('有效', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '评论'
        verbose_name_plural = '评论'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.author} @ {self.post}: {self.content[:20]}'


class Like(models.Model):
    """文章点赞记录。"""

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='文章',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='用户',
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '点赞'
        verbose_name_plural = '点赞'
        # 同一用户对同一文章只能点赞一次
        unique_together = ['post', 'user']

    def __str__(self):
        return f'{self.user} 喜欢 {self.post}'
