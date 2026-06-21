#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys


def main():
    """运行管理命令的入口函数。"""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "template_project.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "无法导入 Django，请确认已安装 Django 且虚拟环境已激活。"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
