"""自定义管理命令：wait_for_db

等待数据库就绪后再继续执行后续操作，常用于容器化部署时
确保数据库已启动后再执行 migrate / runserver。

用法：
    python manage.py wait_for_db
"""

import time

from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):
    """阻塞式等待数据库可用。"""

    help = '等待数据库连接可用'

    def add_arguments(self, parser):
        """定义命令行参数。"""
        parser.add_argument(
            '--timeout',
            type=int,
            default=30,
            help='最长等待秒数（默认 30 秒）',
        )
        parser.add_argument(
            '--interval',
            type=float,
            default=1.0,
            help='每次重试间隔秒数（默认 1.0 秒）',
        )

    def handle(self, *args, **options):
        """命令执行主体。"""
        timeout = options['timeout']
        interval = options['interval']

        self.stdout.write('正在等待数据库就绪...')
        start_time = time.time()

        while True:
            try:
                connection = connections['default']
                connection.ensure_connection()
                self.stdout.write(self.style.SUCCESS('数据库已就绪！'))
                return
            except OperationalError:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    self.stdout.write(self.style.ERROR(
                        f'等待数据库超时（{timeout} 秒），请检查数据库配置。'
                    ))
                    raise

                self.stdout.write(
                    f'数据库暂不可用，{interval:.1f} 秒后重试...'
                    f'（已等待 {elapsed:.1f} 秒）'
                )
                time.sleep(interval)
