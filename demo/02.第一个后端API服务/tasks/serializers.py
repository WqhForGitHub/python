"""Tasks 序列化器 - 将 Model 实例转换为 JSON 可序列化的字典。"""


def task_to_dict(task):
    """将 Task 实例序列化为字典。

    日期时间字段转换为 ISO 8601 字符串，便于前端解析。
    """
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "completed": task.completed,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
    }
