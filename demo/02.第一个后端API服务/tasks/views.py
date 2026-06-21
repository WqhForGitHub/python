"""Tasks API 视图 - 纯 Django 实现的 RESTful CRUD 接口。

不使用 Django REST Framework，手动处理 JSON 解析、数据校验、
序列化与 HTTP 状态码，帮助理解 API 的底层运作原理。

所有 API 视图均使用 @csrf_exempt 豁免 CSRF 校验。
生产环境中应替换为 Token / JWT 等认证机制。
"""

import json

from django.conf import settings
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Task
from .serializers import task_to_dict

# ============================================================
# 允许排序的字段白名单（防止 SQL 注入）
# ============================================================
SORT_FIELDS = {
    "created_at",
    "-created_at",
    "updated_at",
    "-updated_at",
    "title",
    "-title",
    "completed",
    "-completed",
    "id",
    "-id",
}


# ============================================================
# 工具函数
# ============================================================


def parse_json_body(request):
    """解析请求体中的 JSON 数据。

    返回 (data, error_response) 二元组：
    - 成功：data 为 dict，error_response 为 None
    - 失败：data 为 None，error_response 为 JsonResponse
    """
    if not request.body:
        return None, JsonResponse({"error": "请求体不能为空"}, status=400)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return None, JsonResponse({"error": "请求体不是合法的 JSON"}, status=400)
    if not isinstance(data, dict):
        return None, JsonResponse({"error": "请求体必须是一个 JSON 对象"}, status=400)
    return data, None


def validate_task_data(data, partial=False):
    """校验任务数据。

    参数:
        data:    待校验的字典
        partial: 是否为部分更新（PATCH），为 True 时不要求必填字段

    返回 (cleaned_data, errors) 二元组：
    - cleaned_data: 校验通过的字段及值
    - errors:       字段级错误信息字典，为空表示校验通过
    """
    errors = {}
    cleaned = {}

    # ---- title ----
    title = data.get("title")
    if title is None and not partial:
        errors["title"] = "该字段为必填项"
    elif title is not None:
        title = str(title).strip()
        if not title:
            errors["title"] = "标题不能为空"
        elif len(title) > 200:
            errors["title"] = "标题不能超过 200 个字符"
        else:
            cleaned["title"] = title

    # ---- description ----
    description = data.get("description")
    if description is not None:
        cleaned["description"] = str(description)

    # ---- completed ----
    completed = data.get("completed")
    if completed is not None:
        if not isinstance(completed, bool):
            errors["completed"] = "该字段必须为布尔值"
        else:
            cleaned["completed"] = completed

    return cleaned, errors


def get_int_query_param(request, name, default, min_value=1, max_value=None):
    """安全地从查询参数中获取整数值。"""
    raw = request.GET.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    if value < min_value:
        return min_value
    if max_value is not None and value > max_value:
        return max_value
    return value


def json_error(message, status=400, errors=None):
    """构造统一的 JSON 错误响应。"""
    body = {"error": message}
    if errors:
        body["errors"] = errors
    return JsonResponse(body, status=status)


def method_not_allowed(request):
    """返回 405 Method Not Allowed。"""
    return json_error(
        f"不支持的请求方法: {request.method}",
        status=405,
    )


# ============================================================
# API 视图
# ============================================================


@csrf_exempt
def task_list(request):
    """任务列表 & 创建。

    GET  /api/tasks/  → 列表（支持分页 / 过滤 / 搜索 / 排序）
    POST /api/tasks/  → 创建
    """
    if request.method == "GET":
        return _task_list_get(request)
    if request.method == "POST":
        return _task_list_post(request)
    return method_not_allowed(request)


def _task_list_get(request):
    """获取任务列表（带分页、过滤、搜索、排序）。"""
    qs = Task.objects.all()

    # ---- 过滤：按完成状态 ----
    completed = request.GET.get("completed")
    if completed is not None:
        if completed.lower() == "true":
            qs = qs.filter(completed=True)
        elif completed.lower() == "false":
            qs = qs.filter(completed=False)

    # ---- 搜索：按标题模糊匹配 ----
    search = request.GET.get("search")
    if search:
        qs = qs.filter(title__icontains=search)

    # ---- 排序 ----
    sort = request.GET.get("sort", "-created_at")
    if sort not in SORT_FIELDS:
        sort = "-created_at"
    qs = qs.order_by(sort)

    # ---- 分页 ----
    page = get_int_query_param(request, "page", default=1, min_value=1)
    page_size = get_int_query_param(
        request,
        "page_size",
        default=settings.DEFAULT_PAGE_SIZE,
        min_value=1,
        max_value=settings.MAX_PAGE_SIZE,
    )

    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page)

    return JsonResponse(
        {
            "count": paginator.count,
            "page": page_obj.number,
            "page_size": page_size,
            "total_pages": paginator.num_pages,
            "results": [task_to_dict(t) for t in page_obj],
        }
    )


def _task_list_post(request):
    """创建任务。"""
    data, err = parse_json_body(request)
    if err:
        return err

    cleaned, errors = validate_task_data(data)
    if errors:
        return json_error("数据校验失败", errors=errors)

    task = Task.objects.create(**cleaned)
    return JsonResponse(task_to_dict(task), status=201)


@csrf_exempt
def task_detail(request, pk):
    """任务详情 / 更新 / 删除。

    GET    /api/tasks/<pk>/  → 获取单个任务
    PUT    /api/tasks/<pk>/  → 全量更新
    PATCH  /api/tasks/<pk>/  → 部分更新
    DELETE /api/tasks/<pk>/  → 删除
    """
    try:
        task = Task.objects.get(pk=pk)
    except Task.DoesNotExist:
        return json_error(f"任务不存在 (id={pk})", status=404)

    if request.method == "GET":
        return JsonResponse(task_to_dict(task))

    if request.method == "PUT":
        return _task_detail_update(request, task, partial=False)

    if request.method == "PATCH":
        return _task_detail_update(request, task, partial=True)

    if request.method == "DELETE":
        task.delete()
        return JsonResponse(
            {"message": f"任务已删除 (id={pk})"},
            status=200,
        )

    return method_not_allowed(request)


def _task_detail_update(request, task, partial):
    """更新任务（PUT 全量 / PATCH 部分）。"""
    data, err = parse_json_body(request)
    if err:
        return err

    cleaned, errors = validate_task_data(data, partial=partial)
    if errors:
        return json_error("数据校验失败", errors=errors)

    for field, value in cleaned.items():
        setattr(task, field, value)
    task.save()
    return JsonResponse(task_to_dict(task))
