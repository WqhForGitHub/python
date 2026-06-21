"""blog 应用初始迁移：创建 Tag、Post、Comment、Like 模型。"""
from django.conf import settings
from django.db import migrations, models

import django.db.models.deletion


class Migration(migrations.Migration):
    """创建博客核心数据模型。"""

    initial = True

    dependencies = [
        # 依赖 accounts 的自定义用户模型
        ('accounts', '0001_initial'),
        # 可替换依赖：保证 AUTH_USER_MODEL 解析正确
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 标签
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30, unique=True, verbose_name='标签名')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
            ],
            options={
                'verbose_name': '标签',
                'verbose_name_plural': '标签',
                'ordering': ['name'],
            },
        ),
        # 文章（FK 作者，M2M 标签）
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='标题')),
                ('slug', models.SlugField(blank=True, unique=True, verbose_name='slug')),
                ('excerpt', models.CharField(blank=True, max_length=300, verbose_name='摘要')),
                ('content', models.TextField(verbose_name='正文')),
                ('cover', models.ImageField(blank=True, null=True, upload_to='post_covers/', verbose_name='封面图')),
                ('views', models.IntegerField(default=0, verbose_name='浏览量')),
                ('is_published', models.BooleanField(default=True, verbose_name='已发布')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                # 作者外键
                ('author', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='posts',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='作者')),
                # 标签多对多
                ('tags', models.ManyToManyField(
                    blank=True,
                    related_name='posts',
                    to='blog.tag',
                    verbose_name='标签')),
            ],
            options={
                'verbose_name': '文章',
                'verbose_name_plural': '文章',
                'ordering': ['-created_at'],
            },
        ),
        # 评论（自引用父评论实现嵌套）
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(verbose_name='评论内容')),
                ('is_active', models.BooleanField(default=True, verbose_name='有效')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                # 评论者外键
                ('author', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='comments',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='评论者')),
                # 父评论自引用外键
                ('parent', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='replies',
                    to='blog.comment',
                    verbose_name='父评论')),
                # 所属文章外键
                ('post', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='comments',
                    to='blog.post',
                    verbose_name='文章')),
            ],
            options={
                'verbose_name': '评论',
                'verbose_name_plural': '评论',
                'ordering': ['created_at'],
            },
        ),
        # 点赞（unique_together 限制）
        migrations.CreateModel(
            name='Like',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                # 文章外键
                ('post', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='likes',
                    to='blog.post',
                    verbose_name='文章')),
                # 用户外键
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='likes',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='用户')),
            ],
            options={
                'verbose_name': '点赞',
                'verbose_name_plural': '点赞',
                'unique_together': {('post', 'user')},
            },
        ),
    ]
