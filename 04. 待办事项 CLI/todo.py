#!/usr/bin/env python3
"""待办事项 CLI - 纯 Python 实现的命令行待办事项管理工具"""

import argparse
import json
import os
import sys
from datetime import datetime

TODO_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todos.json")


def load_todos():
    """从 JSON 文件加载待办事项列表"""
    if not os.path.exists(TODO_FILE):
        return []
    try:
        with open(TODO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_todos(todos):
    """保存待办事项列表到 JSON 文件"""
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)


def next_id(todos):
    """获取下一个可用 ID"""
    if not todos:
        return 1
    return max(t["id"] for t in todos) + 1


def cmd_add(args):
    """添加一条待办事项"""
    todos = load_todos()
    todo = {
        "id": next_id(todos),
        "task": args.task,
        "done": False,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    todos.append(todo)
    save_todos(todos)
    print(f"  已添加 #{todo['id']}: {todo['task']}")


def cmd_list(args):
    """列出待办事项"""
    todos = load_todos()
    if not todos:
        print("  没有待办事项。使用 add 命令添加新事项。")
        return

    # 筛选
    filter_type = args.filter or "all"
    if filter_type == "done":
        filtered = [t for t in todos if t["done"]]
    elif filter_type == "todo":
        filtered = [t for t in todos if not t["done"]]
    else:
        filtered = todos

    if not filtered:
        labels = {"done": "已完成", "todo": "未完成", "all": ""}
        print(f"  没有{labels.get(filter_type, '')}待办事项。")
        return

    # 统计
    total = len(todos)
    done_count = sum(1 for t in todos if t["done"])
    print(f"\n  待办事项 ({done_count}/{total} 已完成)")
    print("  " + "-" * 40)

    for t in filtered:
        status = "[x]" if t["done"] else "[ ]"
        task_text = t["task"]
        print(f"  {status} #{t['id']:>3}  {task_text}")
        print(f"         创建于 {t['created_at']}")

    print("  " + "-" * 40)
    print()


def cmd_done(args):
    """标记待办事项为已完成"""
    todos = load_todos()
    todo = _find_by_id(todos, args.id)
    if todo is None:
        return
    if todo["done"]:
        print(f"  #{args.id} 已经是完成状态。")
        return
    todo["done"] = True
    todo["done_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    save_todos(todos)
    print(f"  已完成 #{args.id}: {todo['task']}")


def cmd_undo(args):
    """取消完成标记"""
    todos = load_todos()
    todo = _find_by_id(todos, args.id)
    if todo is None:
        return
    if not todo["done"]:
        print(f"  #{args.id} 尚未完成，无需撤销。")
        return
    todo["done"] = False
    todo.pop("done_at", None)
    save_todos(todos)
    print(f"  已撤销完成 #{args.id}: {todo['task']}")


def cmd_delete(args):
    """删除待办事项"""
    todos = load_todos()
    todo = _find_by_id(todos, args.id)
    if todo is None:
        return
    if not args.force:
        confirm = (
            input(f"  确认删除 #{args.id}: {todo['task']}? (y/N) ").strip().lower()
        )
        if confirm != "y":
            print("  已取消。")
            return
    todos = [t for t in todos if t["id"] != args.id]
    save_todos(todos)
    print(f"  已删除 #{args.id}: {todo['task']}")


def cmd_clear(args):
    """清除所有已完成的事项"""
    todos = load_todos()
    done_todos = [t for t in todos if t["done"]]
    if not done_todos:
        print("  没有已完成的事项需要清除。")
        return
    if not args.force:
        print(f"  将清除 {len(done_todos)} 条已完成的事项：")
        for t in done_todos:
            print(f"    [x] #{t['id']}: {t['task']}")
        confirm = input("  确认清除? (y/N) ").strip().lower()
        if confirm != "y":
            print("  已取消。")
            return
    todos = [t for t in todos if not t["done"]]
    save_todos(todos)
    print(f"  已清除 {len(done_todos)} 条已完成的事项。")


def _find_by_id(todos, todo_id):
    """按 ID 查找待办事项，找不到时打印提示"""
    for t in todos:
        if t["id"] == todo_id:
            return t
    print(f"  错误: 找不到 #{todo_id}。使用 list 命令查看所有事项。")
    return None


def build_parser():
    """构建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog="todo",
        description="待办事项 CLI - 简洁的命令行待办管理工具",
    )
    sub = parser.add_subparsers(dest="command", help="可用命令")

    # add
    p_add = sub.add_parser("add", help="添加一条待办事项")
    p_add.add_argument("task", nargs="+", help="待办事项内容")
    p_add.set_defaults(func=cmd_add)

    # list
    p_list = sub.add_parser("list", help="列出待办事项")
    p_list.add_argument(
        "filter",
        nargs="?",
        choices=["all", "done", "todo"],
        default="all",
        help="筛选: all(全部) / done(已完成) / todo(未完成)，默认 all",
    )
    p_list.set_defaults(func=cmd_list)

    # done
    p_done = sub.add_parser("done", help="标记事项为已完成")
    p_done.add_argument("id", type=int, help="事项 ID")
    p_done.set_defaults(func=cmd_done)

    # undo
    p_undo = sub.add_parser("undo", help="取消完成标记")
    p_undo.add_argument("id", type=int, help="事项 ID")
    p_undo.set_defaults(func=cmd_undo)

    # delete
    p_del = sub.add_parser("delete", help="删除一条待办事项")
    p_del.add_argument("id", type=int, help="事项 ID")
    p_del.add_argument("-f", "--force", action="store_true", help="跳过确认提示")
    p_del.set_defaults(func=cmd_delete)

    # clear
    p_clear = sub.add_parser("clear", help="清除所有已完成的事项")
    p_clear.add_argument("-f", "--force", action="store_true", help="跳过确认提示")
    p_clear.set_defaults(func=cmd_clear)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # 将 task 列表合并为字符串（add 命令）
    if hasattr(args, "task") and isinstance(args.task, list):
        args.task = " ".join(args.task)

    args.func(args)


if __name__ == "__main__":
    main()
