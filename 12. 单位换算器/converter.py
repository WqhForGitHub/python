"""
纯 Python 实现的单位换算器（CLI）
支持：长度、重量、温度、面积、体积、时间、速度、数据存储
"""

import sys

# ── 单位定义 ────────────────────────────────────────────────
# 每类单位：{名称: 到基准单位的换算因子}
# 温度特殊处理，用函数代替因子

UNITS: dict[str, dict[str, float]] = {
    "长度": {
        # 基准：米
        "km": 1000,
        "千米": 1000,
        "m": 1,
        "米": 1,
        "dm": 0.1,
        "分米": 0.1,
        "cm": 0.01,
        "厘米": 0.01,
        "mm": 0.001,
        "毫米": 0.001,
        "um": 1e-6,
        "微米": 1e-6,
        "mi": 1609.344,
        "英里": 1609.344,
        "yd": 0.9144,
        "码": 0.9144,
        "ft": 0.3048,
        "英尺": 0.3048,
        "in": 0.0254,
        "英寸": 0.0254,
        "nmi": 1852,
        "海里": 1852,
        "li": 500,
        "里": 500,
    },
    "重量": {
        # 基准：千克
        "t": 1000,
        "吨": 1000,
        "kg": 1,
        "千克": 1,
        "g": 0.001,
        "克": 0.001,
        "mg": 1e-6,
        "毫克": 1e-6,
        "lb": 0.453592,
        "磅": 0.453592,
        "oz": 0.0283495,
        "盎司": 0.0283495,
        "jin": 0.5,
        "斤": 0.5,
    },
    "面积": {
        # 基准：平方米
        "km2": 1e6,
        "平方千米": 1e6,
        "ha": 1e4,
        "公顷": 1e4,
        "mu": 666.667,
        "亩": 666.667,
        "m2": 1,
        "平方米": 1,
        "cm2": 1e-4,
        "平方厘米": 1e-4,
        "ft2": 0.092903,
        "平方英尺": 0.092903,
        "acre": 4046.86,
        "英亩": 4046.86,
    },
    "体积": {
        # 基准：升
        "m3": 1000,
        "立方米": 1000,
        "L": 1,
        "升": 1,
        "mL": 0.001,
        "毫升": 0.001,
        "gal": 3.78541,
        "加仑": 3.78541,
        "qt": 0.946353,
        "夸脱": 0.946353,
        "cup": 0.236588,
        "杯": 0.236588,
        "floz": 0.0295735,
        "液盎司": 0.0295735,
    },
    "时间": {
        # 基准：秒
        "y": 31536000,
        "年": 31536000,
        "mon": 2592000,
        "月": 2592000,
        "w": 604800,
        "周": 604800,
        "d": 86400,
        "天": 86400,
        "h": 3600,
        "小时": 3600,
        "min": 60,
        "分钟": 60,
        "s": 1,
        "秒": 1,
        "ms": 0.001,
        "毫秒": 0.001,
    },
    "速度": {
        # 基准：米/秒
        "m/s": 1,
        "米/秒": 1,
        "km/h": 0.277778,
        "千米/时": 0.277778,
        "mph": 0.44704,
        "英里/时": 0.44704,
        "kn": 0.514444,
        "节": 0.514444,
        "mach": 340.29,
        "马赫": 340.29,
    },
    "数据": {
        # 基准：字节
        "B": 1,
        "字节": 1,
        "KB": 1024,
        "千字节": 1024,
        "MB": 1048576,
        "兆字节": 1048576,
        "GB": 1073741824,
        "吉字节": 1073741824,
        "TB": 1099511627776,
        "太字节": 1099511627776,
        "bit": 0.125,
        "比特": 0.125,
    },
}

# 温度换算函数（特殊处理）
TEMP_UNITS = {"C": "摄氏度", "F": "华氏度", "K": "开尔文"}


# ── 核心计算 ────────────────────────────────────────────────
def convert(value: float, from_unit: str, to_unit: str) -> float:
    """通用单位换算"""
    # 查找单位所属类别
    from_cat = find_category(from_unit)
    to_cat = find_category(to_unit)

    if from_cat is None:
        raise ValueError(f"未知单位：{from_unit}")
    if to_cat is None:
        raise ValueError(f"未知单位：{to_unit}")
    if from_cat != to_cat:
        raise ValueError(f"无法从 {from_cat}({from_unit}) 换算到 {to_cat}({to_unit})")

    # 温度特殊处理
    if from_cat == "温度":
        return convert_temperature(value, from_unit, to_unit)

    # 通用：先转为基准，再转为目标
    base_value = value * UNITS[from_cat][from_unit]
    return base_value / UNITS[to_cat][to_unit]


def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    """温度换算"""
    # 先转为摄氏度
    if from_unit in ("C", "摄氏度"):
        celsius = value
    elif from_unit in ("F", "华氏度"):
        celsius = (value - 32) * 5 / 9
    elif from_unit in ("K", "开尔文"):
        celsius = value - 273.15
    else:
        raise ValueError(f"未知温度单位：{from_unit}")

    # 从摄氏度转为目标
    if to_unit in ("C", "摄氏度"):
        return celsius
    elif to_unit in ("F", "华氏度"):
        return celsius * 9 / 5 + 32
    elif to_unit in ("K", "开尔文"):
        return celsius + 273.15
    else:
        raise ValueError(f"未知温度单位：{to_unit}")


def find_category(unit: str) -> str | None:
    """查找单位所属类别"""
    for cat, units in UNITS.items():
        if unit in units:
            return cat
    # 检查温度
    if unit in TEMP_UNITS:
        return "温度"
    return None


def list_units(category: str | None = None) -> None:
    """列出可用单位"""
    if category:
        if category in UNITS:
            units = UNITS[category]
            base = list(units.values())[0]
            base_name = list(units.keys())[1]  # 中文名
            print(f"\n  {category}（基准：{base_name}）")
            print("  " + "─" * 40)
            for name, factor in units.items():
                if factor != 0:
                    print(f"    {name:<10s}")
        elif category == "温度":
            print(f"\n  温度")
            print("  " + "─" * 40)
            for abbr, name in TEMP_UNITS.items():
                print(f"    {abbr:<5s} {name}")
        else:
            print(f"  未知类别：{category}")
    else:
        print("\n  可用单位类别：")
        print("  " + "─" * 40)
        for cat in list(UNITS.keys()) + ["温度"]:
            print(f"    {cat}")


# ── 交互式 REPL ────────────────────────────────────────────
def repl() -> None:
    print("=" * 52)
    print("  纯 Python 单位换算器 (CLI)")
    print("  输入：数值 源单位 目标单位")
    print("  示例：100 km mi")
    print("  命令：")
    print("  list [类别]  - 查看可用单位")
    print("  q            - 退出")
    print("=" * 52)

    while True:
        try:
            line = input("\n>>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not line:
            continue

        parts = line.split()

        if parts[0].lower() == "q":
            print("再见！")
            break

        # ── 列出单位 ──
        if parts[0].lower() == "list":
            category = parts[1] if len(parts) > 1 else None
            list_units(category)
            continue

        # ── 换算 ──
        if len(parts) >= 3:
            try:
                value = float(parts[0])
                from_unit = parts[1]
                to_unit = parts[2]
                result = convert(value, from_unit, to_unit)

                # 智能格式化
                if abs(result) < 0.001 or abs(result) > 1e9:
                    result_str = f"{result:.6g}"
                else:
                    # 避免浮点精度问题
                    result_str = f"{result:.6f}".rstrip("0").rstrip(".")
                    if result_str == "" or result_str == "-0":
                        result_str = "0"

                print(f"  {value} {from_unit} = {result_str} {to_unit}")
            except ValueError as e:
                print(f"  错误：{e}")
            continue

        print("  用法：<数值> <源单位> <目标单位>，如 100 km mi")
        print("  输入 list 查看所有可用单位")


# ── 命令行入口 ──────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) >= 4:
        try:
            value = float(sys.argv[1])
            from_unit = sys.argv[2]
            to_unit = sys.argv[3]
            result = convert(value, from_unit, to_unit)
            print(f"{value} {from_unit} = {result:.6g} {to_unit}")
        except ValueError as e:
            print(f"错误：{e}", file=sys.stderr)
            sys.exit(1)
    else:
        repl()
