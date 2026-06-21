"""
年龄计算器
根据出生日期计算精确年龄（年/月/天），
显示距下次生日的天数、生肖、星座等信息。
"""

import datetime
import sys

# ── 常量定义 ──────────────────────────────────────────────

ZODIAC_NAMES = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]

ZODIAC_SIGNS = [
    ((1, 20), "水瓶座"),
    ((2, 19), "双鱼座"),
    ((3, 21), "白羊座"),
    ((4, 20), "金牛座"),
    ((5, 21), "双子座"),
    ((6, 22), "巨蟹座"),
    ((7, 23), "狮子座"),
    ((8, 23), "处女座"),
    ((9, 23), "天秤座"),
    ((10, 23), "天蝎座"),
    ((11, 22), "射手座"),
    ((12, 22), "摩羯座"),
]

# ── 计算逻辑 ──────────────────────────────────────────────


def parse_date(date_str: str) -> datetime.date | None:
    """解析日期字符串，支持多种格式。"""
    date_str = date_str.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d"):
        try:
            return datetime.datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def calc_age(
    birth: datetime.date, ref: datetime.date | None = None
) -> tuple[int, int, int]:
    """计算精确年龄，返回 (年, 月, 日)。"""
    if ref is None:
        ref = datetime.date.today()
    years = ref.year - birth.year
    months = ref.month - birth.month
    days = ref.day - birth.day

    if days < 0:
        months -= 1
        # 获取上个月的天数
        prev_month = ref.month - 1 if ref.month > 1 else 12
        prev_year = ref.year if ref.month > 1 else ref.year - 1
        days_in_prev = (
            datetime.date(prev_year, prev_month + 1, 1)
            - datetime.date(prev_year, prev_month, 1)
        ).days
        days += days_in_prev

    if months < 0:
        years -= 1
        months += 12

    return years, months, days


def days_until_birthday(birth: datetime.date, ref: datetime.date | None = None) -> int:
    """计算距离下次生日的天数。"""
    if ref is None:
        ref = datetime.date.today()
    try:
        next_birthday = datetime.date(ref.year, birth.month, birth.day)
    except ValueError:
        # 处理 2月29日 在非闰年的情况
        next_birthday = datetime.date(ref.year, 3, 1)

    if next_birthday <= ref:
        try:
            next_birthday = datetime.date(ref.year + 1, birth.month, birth.day)
        except ValueError:
            next_birthday = datetime.date(ref.year + 1, 3, 1)

    return (next_birthday - ref).days


def get_zodiac(year: int) -> str:
    """根据年份获取生肖。"""
    return ZODIAC_NAMES[(year - 4) % 12]


def get_constellation(month: int, day: int) -> str:
    """根据月日获取星座。"""
    for (m, d), sign in ZODIAC_SIGNS:
        if (month, day) < (m, d):
            # 取上一个星座
            idx = ZODIAC_SIGNS.index(((m, d), sign))
            if idx == 0:
                return ZODIAC_SIGNS[-1][1]
            return ZODIAC_SIGNS[idx - 1][1]
    return ZODIAC_SIGNS[-1][1]


def total_days_lived(birth: datetime.date, ref: datetime.date | None = None) -> int:
    """计算已经生活的总天数。"""
    if ref is None:
        ref = datetime.date.today()
    return (
        (ref - birth).date().days
        if isinstance(ref, datetime.datetime)
        else (ref - birth).days
    )


# ── 结果展示 ──────────────────────────────────────────────


def show_age_info(birth: datetime.date, ref: datetime.date | None = None) -> None:
    """展示完整的年龄信息。"""
    if ref is None:
        ref = datetime.date.today()

    years, months, days = calc_age(birth, ref)
    total_days = total_days_lived(birth, ref)
    days_to_bday = days_until_birthday(birth, ref)
    zodiac = get_zodiac(birth.year)
    constellation = get_constellation(birth.month, birth.day)

    total_hours = total_days * 24
    total_weeks = total_days // 7

    print(f"\n  ═══ 年龄信息 ═══")
    print(f"  出生日期：{birth.strftime('%Y-%m-%d')}")
    print(f"  参照日期：{ref.strftime('%Y-%m-%d')}")
    print(f"  ─────────────────────")
    print(f"  精确年龄：{years} 岁 {months} 个月 {days} 天")
    print(f"  总天数  ：{total_days:,} 天")
    print(f"  总周数  ：{total_weeks:,} 周")
    print(f"  总小时  ：{total_hours:,} 小时")
    print(f"  ─────────────────────")
    print(f"  生肖：{zodiac}")
    print(f"  星座：{constellation}")
    print(f"  ─────────────────────")

    if days_to_bday == 0:
        print("  今天是你的生日！生日快乐！")
    else:
        print(f"  距下次生日还有 {days_to_bday} 天")
    print()


# ── 主菜单 ────────────────────────────────────────────────


def print_menu() -> None:
    today = datetime.date.today()
    print("=" * 40)
    print(f"  年龄计算器    {today.strftime('%Y-%m-%d')}")
    print("=" * 40)
    print("  1. 计算年龄")
    print("  2. 计算两个日期之间的间隔")
    print("  3. 批量计算年龄")
    print("  q. 退出")
    print("-" * 40)


def input_date(prompt: str) -> datetime.date | None:
    """输入日期，返回 date 对象。"""
    raw = input(prompt).strip()
    if raw.lower() == "q":
        return None
    date = parse_date(raw)
    if date is None:
        print("  日期格式无效，请使用 YYYY-MM-DD 格式")
        return None
    return date


def main() -> None:
    while True:
        print_menu()
        choice = input("  请选择: ").strip()

        if choice == "q":
            print("  再见！")
            break

        elif choice == "1":
            birth = input_date("  请输入出生日期（如 2000-01-15）: ")
            if birth:
                if birth > datetime.date.today():
                    print("  出生日期不能晚于今天")
                else:
                    show_age_info(birth)

        elif choice == "2":
            start = input_date("  起始日期: ")
            if start is None:
                continue
            end = input_date("  结束日期: ")
            if end is None:
                continue
            delta = abs((end - start).days)
            years = delta // 365
            months = delta // 30
            weeks = delta // 7
            print(f"\n  日期间隔：{delta:,} 天")
            print(f"  约 {years} 年 / {months} 个月 / {weeks} 周\n")

        elif choice == "3":
            print("  输入多个出生日期，每行一个，输入空行结束：")
            birthdays = []
            while True:
                raw = input("  > ").strip()
                if not raw:
                    break
                date = parse_date(raw)
                if date and date <= datetime.date.today():
                    birthdays.append(date)
                elif date:
                    print("  日期不能晚于今天")
                else:
                    print("  格式无效")
            if birthdays:
                print()
                for b in birthdays:
                    y, m, d = calc_age(b)
                    print(f"  {b.strftime('%Y-%m-%d')} → {y} 岁 {m} 个月 {d} 天")
                print()

        else:
            print("  无效选择，请重新输入")


if __name__ == "__main__":
    main()
