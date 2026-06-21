"""core 应用视图。

包含首页、关于页面，以及自定义的 404 / 500 错误处理函数。
"""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def home(request: HttpRequest) -> HttpResponse:
    """首页视图。"""
    return render(
        request,
        "core/home.html",
        {
            "page_title": "首页",
        },
    )


def about(request: HttpRequest) -> HttpResponse:
    """关于页面视图。"""
    return render(
        request,
        "core/about.html",
        {
            "page_title": "关于",
        },
    )


def handler404(request: HttpRequest, exception=None) -> HttpResponse:
    """自定义 404 处理器。"""
    return render(request, "404.html", status=404)


def handler500(request: HttpRequest) -> HttpResponse:
    """自定义 500 处理器。"""
    return render(request, "500.html", status=500)
