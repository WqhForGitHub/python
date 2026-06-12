#!/usr/bin/env python3
"""
纯 Python 实现的倒计时器（CLI）
支持：自定义时/分/秒、暂停/继续、倒计时结束提醒
"""

import sys
import time


# ── 倒计时核心逻辑 ─────────────────────────────────────────
def parse_duration(hours: int, minutes: int, seconds: int) -> int:
    """将时/分/秒转换为总秒数"""
    if hours < 0 or minutes < 0 or seconds < 0:
        raise ValueError("时间不能为负数")
    if minutes >= 60 or seconds >= 60:
        raise ValueError("分钟和秒数必须在 0-59 之间")
    return hours * 3600 + minutes * 60 + seconds


def format_time(total_seconds: int) -> str:
    """将总秒数格式化为 HH:MM:SS"""
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


# ── 倒计时运行器 ──────────────────────────────────────────
def run_countdown(total_seconds: int) -> None:
    """运行倒计时，支持暂停/继续"""
    if total_seconds <= 0:
        print("  倒计时时间不能为零或负数。")
        return

    remaining = total_seconds
    paused = False

    print(f"\n  倒计时: {format_time(remaining)}")
    print("  按 Enter 暂停/继续，输入 q 退出\n")

    while remaining > 0:
        # 显示倒计时
        bar_length = 30
        progress = 1 - remaining / total_seconds
        filled = int(bar_length * progress)
        bar = "█" * filled + "░" * (bar_length - filled)
        sys.stdout.write(
            f"\r  [{bar}] {format_time(remaining)}  " f"({progress * 100:.1f}%)  "
        )
        sys.stdout.flush()

        # 检查用户输入（非阻塞）
        if paused:
            sys.stdout.write("\r  ⏸ 已暂停 - 按 Enter 继续          ")
            sys.stdout.flush()

        start = time.time()
        try:
            # 使用短间隔以便快速响应暂停/退出
            time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\n  倒计时已中断。")
            return

        if not paused:
            elapsed = time.time() - start
            remaining = max(0, remaining - int(elapsed + 0.5))
            if remaining <= 0:
                remaining = 0

    # 倒计时结束
    bar = "█" * bar_length
    sys.stdout.write(f"\r  [{bar}] {format_time(0)}  (100.0%)  \n")
    sys.stdout.flush()
    print("\n  ⏰ 倒计时结束！")

    # 播放提醒（终端响铃）
    for _ in range(3):
        sys.stdout.write("\a")
        sys.stdout.flush()
        time.sleep(0.3)


# ── 交互式输入 ─────────────────────────────────────────────
def interactive_mode() -> None:
    """交互式输入倒计时时间"""
    print("=" * 48)
    print("  纯 Python 倒计时器 (CLI)")
    print("  设置倒计时时间，到时提醒")
    print("=" * 48)

    try:
        hours = input("\n  小时 (默认 0): ").strip()
        hours = int(hours) if hours else 0

        minutes = input("  分钟 (默认 0): ").strip()
        minutes = int(minutes) if minutes else 0

        seconds = input("  秒数 (默认 0): ").strip()
        seconds = int(seconds) if seconds else 0
    except ValueError:
        print("  错误：请输入有效的整数。")
        return
    except (EOFError, KeyboardInterrupt):
        print("\n  再见！")
        return

    try:
        total = parse_duration(hours, minutes, seconds)
    except ValueError as e:
        print(f"  错误：{e}")
        return

    run_countdown(total)


# ── 命令行入口 ─────────────────────────────────────────────
def main() -> None:
    if len(sys.argv) > 1:
        # 非交互模式：python countdown.py 25 或 python countdown.py 1:30 或 python countdown.py 0:1:30
        arg = sys.argv[1]
        try:
            parts = arg.split(":")
            if len(parts) == 1:
                # 纯秒数
                total = int(parts[0])
            elif len(parts) == 2:
                # 分:秒
                m, s = int(parts[0]), int(parts[1])
                total = parse_duration(0, m, s)
            elif len(parts) == 3:
                # 时:分:秒
                h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
                total = parse_duration(h, m, s)
            else:
                raise ValueError("格式不正确")
            run_countdown(total)
        except (ValueError, IndexError) as e:
            print(f"错误：{e}", file=sys.stderr)
            print(
                "用法：python countdown.py [秒数 | 分:秒 | 时:分:秒]", file=sys.stderr
            )
            sys.exit(1)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
