"""项目级视图 - API 根路径、健康检查、自定义 JSON 错误处理器。"""

from django.conf import settings
from django.http import JsonResponse


def api_root(request):
    """API 根路径 - 返回接口信息与可用端点列表。"""
    return JsonResponse({
        'name': '第一个后端API服务',
        'version': '1.0.0',
        'description': '使用纯 Django 实现的 Task CRUD RESTful API',
        'endpoints': {
            'health': '/api/health/',
            'tasks': '/api/tasks/',
            'task_detail': '/api/tasks/{id}/',
            'admin': '/admin/',
        },
    })


def health_check(request):
    """健康检查端点。"""
    return JsonResponse({'status': 'ok'})


# ============================================================
# 自定义 JSON 错误处理器
# ============================================================
# 当 DEBUG=False 时，Django 会使用这些处理器返回 JSON 格式的错误响应，
# 而非默认的 HTML 页面，确保 API 错误响应风格一致。

def json_404(request, exception=None):
    """全局 404 处理器 - 返回 JSON。"""
    return JsonResponse(
        {'error': '资源不存在', 'path': request.path},
        status=404,
    )


def json_500(request):
    """全局 500 处理器 - 返回 JSON。"""
    return JsonResponse(
        {'error': '服务器内部错误'},
        status=500,
    )
