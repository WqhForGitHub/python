"""初始化迁移 - 创建 Task 表。"""

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='标题')),
                ('description', models.TextField(blank=True, default='', verbose_name='描述')),
                ('completed', models.BooleanField(default=False, verbose_name='是否完成')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '任务',
                'verbose_name_plural': '任务',
                'ordering': ['-created_at'],
            },
        ),
    ]
