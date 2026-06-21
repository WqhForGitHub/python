"""
简单日历生成器
支持按月/按年查看日历，可高亮当天日期，
支持跳转到指定月份查看。
"""

import calendar
import datetime
import sys

# ── 辅助函数 ──────────────────────────────────────────────


def get_today() -> datetime.date:
    """获取今天的日期。"""
    return datetime.date.today()


def is_today(year: int, month: int, day: int) -> bool:
    """判断给定日期是否为今天。"""
    today = get_today()
    return year == today.year and month == today.month and day == today.day


# ── 日历展示 ──────────────────────────────────────────────


def show_month(year: int, month: int, highlight: bool = True) -> None:
    """展示指定月份的日历，可选择高亮今天。"""
    cal = calendar.monthcalendar(year, month)
    month_names = [
        "",
        "一月",
        "二月",
        "三月",
        "四月",
        "五月",
        "六月",
        "七月",
        "八月",
        "九月",
        "十月",
        "十一月",
        "十二月",
    ]
    weekdays = ["一", "二", "三", "四", "五", "六", "日"]

    today = get_today()
    is_current_month = year == today.year and month == today.month

    header = f"  {year} 年 {month_names[month]}"
    print(header)
    print("  " + "  ".join(weekdays))

    for week in cal:
        line = []
        for i, day in enumerate(week):
            if day == 0:
                line.append("  ")
            elif highlight and is_current_month and day == today.day:
                line.append(f"[{day:2d}]")
            else:
                line.append(f" {day:2d} ")
        print("  " + "".join(line))
    print()


def show_year(year: int) -> None:
    """展示指定年份的完整日历。"""
    print(f"\n  ═══ {year} 年 日历 ═══\n")
    for month in range(1, 13):
        show_month(year, month, highlight=True)
        if month < 12:
            print()


def show_range(start_year: int, start_month: int, count: int) -> None:
    """展示从指定月份开始的连续 count 个月日历。"""
    year, month = start_year, start_month
    for _ in range(count):
        show_month(year, month)
        month += 1
        if month > 12:
            month = 1
            year += 1


# ── 年历紧凑展示 ──────────────────────────────────────────


def show_year_compact(year: int) -> None:
    """以紧凑格式展示全年日历（每行3个月）。"""
    month_names = [
        "",
        " 1月",
        " 2月",
        " 3月",
        " 4月",
        " 5月",
        " 6月",
        " 7月",
        " 8月",
        " 9月",
        "10月",
        "11月",
        "12月",
    ]
    weekdays = "一 二 三 四 五 六 日"

    today = get_today()
    print(f"\n  ═══ {year} 年 ═══\n")

    for row in range(0, 12, 3):
        # 打印月份标题
        titles = []
        for m in range(row + 1, row + 4):
            titles.append(f"{month_names[m]:^22}")
        print("  " + "".join(titles))

        # 打印星期标题
        print("  " + (f"{weekdays:^22}" * 3))

        cals = [calendar.monthcalendar(year, m) for m in range(row + 1, row + 4)]

        max_weeks = max(len(c) for c in cals)
        for w in range(max_weeks):
            line_parts = []
            for ci in range(3):
                if w < len(cals[ci]):
                    week_str = ""
                    for day in cals[ci][w]:
                        if day == 0:
                            week_str += "   "
                        elif (
                            year == today.year
                            and (row + ci + 1) == today.month
                            and day == today.day
                        ):
                            week_str += f"[{day:2d}]"
                        else:
                            week_str += f" {day:2d}"
                    line_parts.append(f"{week_str:^22}")
                else:
                    line_parts.append(f"{'':^22}")
            print("  " + "".join(line_parts))
        print()


# ── 主菜单 ────────────────────────────────────────────────


def print_menu() -> None:
    today = get_today()
    print("=" * 45)
    print(f"  简单日历生成器    今天: {today.strftime('%Y-%m-%d')}")
    print("=" * 45)
    print("  1. 查看当月日历")
    print("  2. 查看指定月份日历")
    print("  3. 查看全年日历（紧凑）")
    print("  4. 查看全年日历（详细）")
    print("  5. 查看连续N个月日历")
    print("  6. 上/下月切换")
    print("  q. 退出")
    print("-" * 45)


def input_year_month() -> tuple[int, int]:
    """输入年份和月份。"""
    today = get_today()
    raw_y = input(f"  年份（默认{today.year}）: ").strip()
    year = int(raw_y) if raw_y else today.year
    raw_m = input(f"  月份（默认{today.month}）: ").strip()
    month = int(raw_m) if raw_m else today.month
    if not (1 <= month <= 12):
        print("  月份必须在 1-12 之间")
        return today.year, today.month
    if year < 1 or year > 9999:
        print("  年份超出范围")
        return today.year, today.month
    return year, month


def main() -> None:
    today = get_today()
    current_year, current_month = today.year, today.month

    while True:
        print_menu()
        choice = input("  请选择: ").strip()

        if choice == "q":
            print("  再见！")
            break

        elif choice == "1":
            show_month(current_year, current_month)

        elif choice == "2":
            try:
                year, month = input_year_month()
                current_year, current_month = year, month
                show_month(year, month)
            except ValueError:
                print("  输入无效，请输入数字")

        elif choice == "3":
            try:
                raw = input(f"  年份（默认{today.year}）: ").strip()
                year = int(raw) if raw else today.year
                show_year_compact(year)
            except ValueError:
                print("  输入无效")

        elif choice == "4":
            try:
                raw = input(f"  年份（默认{today.year}）: ").strip()
                year = int(raw) if raw else today.year
                show_year(year)
            except ValueError:
                print("  输入无效")

        elif choice == "5":
            try:
                raw = input(f"  起始年份（默认{current_year}）: ").strip()
                year = int(raw) if raw else current_year
                raw = input(f"  起始月份（默认{current_month}）: ").strip()
                month = int(raw) if raw else current_month
                raw = input("  显示几个月: ").strip()
                count = int(raw) if raw else 3
                show_range(year, month, count)
            except ValueError:
                print("  输入无效")

        elif choice == "6":
            show_month(current_year, current_month)
            while True:
                nav = input("  < 上月 | > 下月 | q 返回: ").strip()
                if nav in ("<", "a", "左"):
                    current_month -= 1
                    if current_month < 1:
                        current_month = 12
                        current_year -= 1
                    show_month(current_year, current_month)
                elif nav in (">", "d", "右"):
                    current_month += 1
                    if current_month > 12:
                        current_month = 1
                        current_year += 1
                    show_month(current_year, current_month)
                elif nav == "q":
                    break

        else:
            print("  无效选择，请重新输入")


if __name__ == "__main__":
    main()
