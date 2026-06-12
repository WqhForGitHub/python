"""
掷骰子模拟器
支持多种骰子类型（D4/D6/D8/D10/D12/D20/D100），
可自定义骰子数量，显示投掷结果与统计信息。
"""

import random
import sys

# ── 骰子类型定义 ──────────────────────────────────────────

DICE_TYPES = {
    "1": ("D4", 4),
    "2": ("D6", 6),
    "3": ("D8", 8),
    "4": ("D10", 10),
    "5": ("D12", 12),
    "6": ("D20", 20),
    "7": ("D100", 100),
}

# ── 投掷逻辑 ──────────────────────────────────────────────


def roll_dice(sides: int, count: int = 1) -> list[int]:
    """投掷指定面数和数量的骰子，返回结果列表。"""
    return [random.randint(1, sides) for _ in range(count)]


def roll_custom(expression: str) -> tuple[list[int], int, int]:
    """
    解析骰子表达式（如 2d6、3d20），返回 (结果列表, 骰子数, 面数)。
    """
    expression = expression.strip().lower()
    try:
        if "d" in expression:
            parts = expression.split("d")
            count = int(parts[0]) if parts[0] else 1
            sides = int(parts[1])
        else:
            count = 1
            sides = int(expression)
        if count < 1 or count > 100:
            print("  错误：骰子数量范围为 1-100")
            return [], 0, 0
        if sides < 2 or sides > 1000:
            print("  错误：骰子面数范围为 2-1000")
            return [], 0, 0
        results = roll_dice(sides, count)
        return results, count, sides
    except (ValueError, IndexError):
        print("  错误：表达式格式不正确，请使用如 2d6、3d20 的格式")
        return [], 0, 0


# ── 结果展示 ──────────────────────────────────────────────


def show_results(results: list[int], sides: int, count: int) -> None:
    """展示投掷结果与统计信息。"""
    total = sum(results)
    print(f"\n  投掷 {count}D{sides}：")
    print(f"  结果：{results}")
    print(f"  总和：{total}")
    if count > 1:
        print(f"  平均：{total / count:.2f}")
        print(f"  最小：{min(results)}  最大：{max(results)}")
    print()


# ── 骰子图案 ──────────────────────────────────────────────

D6_ART = {
    1: ["┌─────┐", "│     │", "│  ●  │", "│     │", "└─────┘"],
    2: ["┌─────┐", "│    ●│", "│     │", "│●    │", "└─────┘"],
    3: ["┌─────┐", "│    ●│", "│  ●  │", "│●    │", "└─────┘"],
    4: ["┌─────┐", "│●  ●│", "│     │", "│●  ●│", "└─────┘"],
    5: ["┌─────┐", "│●  ●│", "│  ●  │", "│●  ●│", "└─────┘"],
    6: ["┌─────┐", "│●  ●│", "│●  ●│", "│●  ●│", "└─────┘"],
}


def show_d6_face(value: int) -> None:
    """显示 D6 骰子的 ASCII 图案。"""
    if value in D6_ART:
        for line in D6_ART[value]:
            print(f"    {line}")


# ── 主菜单 ────────────────────────────────────────────────


def print_menu() -> None:
    print("=" * 40)
    print("  掷骰子模拟器")
    print("=" * 40)
    print("  1. D4    2. D6    3. D8")
    print("  4. D10   5. D12   6. D20")
    print("  7. D100")
    print("  8. 自定义表达式（如 2d6）")
    print("  q. 退出")
    print("-" * 40)


def get_count() -> int:
    """获取骰子数量。"""
    while True:
        raw = input("  骰子数量（默认1）: ").strip()
        if not raw:
            return 1
        try:
            count = int(raw)
            if 1 <= count <= 100:
                return count
            print("  请输入 1-100 之间的整数")
        except ValueError:
            print("  请输入有效数字")


def main() -> None:
    history: list[tuple[str, list[int]]] = []

    while True:
        print_menu()
        choice = input("  请选择骰子类型: ").strip()

        if choice == "q":
            print("  再见！")
            break

        if choice in DICE_TYPES:
            name, sides = DICE_TYPES[choice]
            count = get_count()
            results = roll_dice(sides, count)
            show_results(results, sides, count)
            history.append((f"{count}{name}", results))
            if name == "D6" and count <= 5:
                for i, val in enumerate(results):
                    print(f"  第 {i + 1} 个骰子：")
                    show_d6_face(val)

        elif choice == "8":
            expr = input("  输入骰子表达式（如 2d6、3d20）: ").strip()
            if expr.lower() == "q":
                continue
            results, count, sides = roll_custom(expr)
            if results:
                show_results(results, sides, count)
                history.append((f"{count}D{sides}", results))

        elif choice == "h":
            if not history:
                print("  暂无投掷记录")
            else:
                print("\n  投掷历史：")
                for i, (desc, res) in enumerate(history[-10:], 1):
                    total = sum(res)
                    print(f"  {i}. {desc} → {res} (总和: {total})")
            print()

        else:
            print("  无效选择，请重新输入")


if __name__ == "__main__":
    main()
