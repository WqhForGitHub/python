#!/usr/bin/env python3
"""
纯 Python 实现的闹钟（CLI）
支持：设置闹钟时间、倒计时显示、到时提醒、多闹钟管理
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta

ALARM_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alarms.json")


# ── 闹钟数据持久化 ─────────────────────────────────────────
def load_alarms() -> list[dict]:
    """从 JSON 文件加载闹钟列表"""
    if not os.path.exists(ALARM_FILE):
        return []
    try:
        with open(ALARM_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_alarms(alarms: list[dict]) -> None:
    """保存闹钟列表到 JSON 文件"""
    with open(ALARM_FILE, "w", encoding="utf-8") as f:
        json.dump(alarms, f, ensure_ascii=False, indent=2)


def next_id(alarms: list[dict]) -> int:
    """获取下一个可用 ID"""
    if not alarms:
        return 1
    return max(a["id"] for a in alarms) + 1


# ── 时间工具 ───────────────────────────────────────────────
def parse_time_str(time_str: str) -> tuple[int, int]:
    """解析时间字符串 HH:MM，返回 (时, 分)"""
    parts = time_str.strip().split(":")
    if len(parts) != 2:
        raise ValueError("时间格式应为 HH:MM")
    h, m = int(parts[0]), int(parts[1])
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError("小时范围 0-23，分钟范围 0-59")
    return h, m


def seconds_until(h: int, m: int) -> int:
    """计算从现在到指定时:分 的剩余秒数"""
    now = datetime.now()
    target = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)  # 如果已过则设为明天
    return int((target - now).total_seconds())


def format_remaining(secs: int) -> str:
    """将秒数格式化为可读的倒计时字符串"""
    if secs <= 0:
        return "00:00:00"
    h = secs // 3600
    m = (secs % 3600) // 60
    s = secs % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


# ── 闹钟命令 ───────────────────────────────────────────────
def cmd_add(args) -> None:
    """添加一个闹钟"""
    try:
        h, m = parse_time_str(args.time)
    except ValueError as e:
        print(f"  错误：{e}")
        return

    alarms = load_alarms()
    alarm = {
        "id": next_id(alarms),
        "time": f"{h:02d}:{m:02d}",
        "label": args.label or "闹钟",
        "enabled": True,
    }
    alarms.append(alarm)
    save_alarms(alarms)

    remaining = seconds_until(h, m)
    print(f"  已添加闹钟 #{alarm['id']}: {alarm['time']} - {alarm['label']}")
    print(f"  距离响铃还有 {format_remaining(remaining)}")


def cmd_list(args) -> None:
    """列出所有闹钟"""
    alarms = load_alarms()
    if not alarms:
        print("  没有设置闹钟。使用 add 命令添加闹钟。")
        return

    print(f"\n  闹钟列表 ({len(alarms)} 个)")
    print("  " + "-" * 44)

    now = datetime.now()
    for a in alarms:
        status = "启用" if a["enabled"] else "禁用"
        h, m = int(a["time"].split(":")[0]), int(a["time"].split(":")[1])
        remaining = seconds_until(h, m) if a["enabled"] else -1
        remaining_str = format_remaining(remaining) if a["enabled"] else "--:--:--"
        print(
            f"  {'[ON] ' if a['enabled'] else '[OFF]'} #{a['id']:>3}  "
            f"{a['time']}  {a['label']:<12}  剩余 {remaining_str}"
        )

    print("  " + "-" * 44)
    print()


def cmd_delete(args) -> None:
    """删除一个闹钟"""
    alarms = load_alarms()
    alarm = _find_by_id(alarms, args.id)
    if alarm is None:
        return
    alarms = [a for a in alarms if a["id"] != args.id]
    save_alarms(alarms)
    print(f"  已删除闹钟 #{args.id}: {alarm['time']} - {alarm['label']}")


def cmd_toggle(args) -> None:
    """启用/禁用闹钟"""
    alarms = load_alarms()
    alarm = _find_by_id(alarms, args.id)
    if alarm is None:
        return
    alarm["enabled"] = not alarm["enabled"]
    save_alarms(alarms)
    status = "启用" if alarm["enabled"] else "禁用"
    print(f"  已{status}闹钟 #{args.id}: {alarm['time']} - {alarm['label']}")


def cmd_run(args) -> None:
    """运行闹钟监控，等待最近的闹钟响铃"""
    alarms = load_alarms()
    enabled = [a for a in alarms if a["enabled"]]
    if not enabled:
        print("  没有启用的闹钟。使用 add 命令添加闹钟。")
        return

    # 找到最近的闹钟
    now = datetime.now()
    nearest = None
    nearest_secs = float("inf")
    for a in enabled:
        h, m = int(a["time"].split(":")[0]), int(a["time"].split(":")[1])
        secs = seconds_until(h, m)
        if secs < nearest_secs:
            nearest_secs = secs
            nearest = a

    print(f"  等待最近的闹钟: #{nearest['id']} {nearest['time']} - {nearest['label']}")
    print(f"  距离响铃还有 {format_remaining(nearest_secs)}")
    print("  按 Ctrl+C 退出\n")

    try:
        while nearest_secs > 0:
            now = datetime.now()
            h, m = int(nearest["time"].split(":")[0]), int(
                nearest["time"].split(":")[1]
            )
            nearest_secs = seconds_until(h, m)

            if nearest_secs <= 0:
                break

            sys.stdout.write(
                f"\r  ⏰ {nearest['label']} 将在 {format_remaining(nearest_secs)} 后响铃  "
            )
            sys.stdout.flush()
            time.sleep(1)

        # 闹钟响铃
        print(f"\n\n  🔔 闹钟响铃！{nearest['time']} - {nearest['label']}")
        print("  🔔🔔🔔")
        for _ in range(5):
            sys.stdout.write("\a")
            sys.stdout.flush()
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n  闹钟监控已停止。")


def _find_by_id(alarms: list[dict], alarm_id: int) -> dict | None:
    """按 ID 查找闹钟"""
    for a in alarms:
        if a["id"] == alarm_id:
            return a
    print(f"  错误: 找不到闹钟 #{alarm_id}。使用 list 命令查看所有闹钟。")
    return None


# ── 命令行参数解析 ─────────────────────────────────────────
def build_parser():
    import argparse

    parser = argparse.ArgumentParser(
        prog="alarm",
        description="纯 Python 闹钟 (CLI) - 命令行闹钟管理工具",
    )
    sub = parser.add_subparsers(dest="command", help="可用命令")

    # add
    p_add = sub.add_parser("add", help="添加闹钟")
    p_add.add_argument("time", help="闹钟时间 (HH:MM)")
    p_add.add_argument("-l", "--label", help="闹钟标签", default=None)
    p_add.set_defaults(func=cmd_add)

    # list
    p_list = sub.add_parser("list", help="列出所有闹钟")
    p_list.set_defaults(func=cmd_list)

    # delete
    p_del = sub.add_parser("delete", help="删除闹钟")
    p_del.add_argument("id", type=int, help="闹钟 ID")
    p_del.set_defaults(func=cmd_delete)

    # toggle
    p_toggle = sub.add_parser("toggle", help="启用/禁用闹钟")
    p_toggle.add_argument("id", type=int, help="闹钟 ID")
    p_toggle.set_defaults(func=cmd_toggle)

    # run
    p_run = sub.add_parser("run", help="运行闹钟监控")
    p_run.set_defaults(func=cmd_run)

    return parser


# ── 主入口 ─────────────────────────────────────────────────
def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
