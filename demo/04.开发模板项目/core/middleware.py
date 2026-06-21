"""自定义中间件。

RequestTimingMiddleware：测量每个请求的处理耗时，并通过响应头返回。
"""

import time

from django.http import HttpRequest, HttpResponse


class RequestTimingMiddleware:
    """在响应头中注入 X-Request-Duration，单位为毫秒。

    演示中间件的基本写法：实现 __init__ 与 __call__ 钩子。
    """

    def __init__(self, get_response):
        """中间件初始化，仅在项目启动时执行一次。"""
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """每个请求都会执行：记录开始时间 -> 处理请求 -> 计算耗时。"""
        start_time = time.perf_counter()

        response = self.get_response(request)

        duration_ms = (time.perf_counter() - start_time) * 1000
        response["X-Request-Duration"] = f"{duration_ms:.2f}ms"
        return response
