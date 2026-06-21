"""
accounts 应用 - 第二个迁移：为 User 添加 department 外键。

依赖 accounts/0001_initial 与 employees/0001_initial，
解决 User 与 Department 的循环依赖。
"""
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('employees', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='department',
            field=models.ForeignKey(
                blank=True,
                help_text='',
                null=True,
                on_delete=models.SET_NULL,
                related_name='members',
                to='employees.department',
                verbose_name='所属部门',
            ),
        ),
    ]
