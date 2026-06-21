#!/usr/bin/env python
"""Django 命令行管理工具。"""
import os
import sys


def main():
    """运行管理命令的入口。"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin_project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "无法导入 Django，请确认已安装 Django 并且虚拟环境已激活。"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
