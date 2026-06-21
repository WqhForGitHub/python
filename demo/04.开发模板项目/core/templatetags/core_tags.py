"""core 应用自定义模板标签库。

使用方式：在模板顶部 {% load core_tags %}，然后使用 {% current_year %}。
"""

from datetime import datetime

from django import template

register = template.Library()


@register.simple_tag
def current_year() -> int:
    """返回当前年份，常用于页脚版权信息。"""
    return datetime.now().year
