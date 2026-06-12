"""
纯 Python 实现的 BMI 计算器（CLI）
支持：公制/英制单位、BMI 分类、健康建议、交互式 REPL
"""

import sys

# ── BMI 分类标准（WHO）──────────────────────────────────────
CATEGORIES = [
    (15.0, "非常严重偏瘦", "⚠ 体重过低，存在严重健康风险"),
    (16.0, "严重偏瘦", "⚠ 体重过低，需要增加营养摄入"),
    (18.5, "偏瘦", "体重偏低，建议适当增加体重"),
    (25.0, "正常", "体重健康，请继续保持"),
    (30.0, "偏胖", "体重偏高，建议控制饮食并增加运动"),
    (35.0, "肥胖 I 级", "⚠ 肥胖，建议咨询医生制定减重计划"),
    (40.0, "肥胖 II 级", "⚠ 严重肥胖，请尽快就医"),
    (float("inf"), "肥胖 III 级", "⚠ 极度肥胖，请立即就医"),
]


# ── 核心计算 ────────────────────────────────────────────────
def calc_bmi_metric(weight_kg: float, height_m: float) -> float:
    """公制：体重(kg) / 身高(m)^2"""
    if height_m <= 0:
        raise ValueError("身高必须大于 0")
    if weight_kg <= 0:
        raise ValueError("体重必须大于 0")
    return weight_kg / (height_m**2)


def calc_bmi_imperial(weight_lb: float, height_in: float) -> float:
    """英制：体重(lb) × 703 / 身高(in)^2"""
    if height_in <= 0:
        raise ValueError("身高必须大于 0")
    if weight_lb <= 0:
        raise ValueError("体重必须大于 0")
    return weight_lb * 703 / (height_in**2)


def classify(bmi: float) -> tuple[str, str]:
    """根据 BMI 值返回 (分类名称, 健康建议)"""
    for threshold, label, advice in CATEGORIES:
        if bmi < threshold:
            return label, advice
    return CATEGORIES[-1][1], CATEGORIES[-1][2]


def ideal_weight_range(height_m: float) -> tuple[float, float]:
    """根据身高计算正常 BMI 范围（18.5-24.9）对应的体重范围(kg)"""
    low = 18.5 * height_m**2
    high = 24.9 * height_m**2
    return low, high


# ── 格式化输出 ──────────────────────────────────────────────
def bmi_bar(bmi: float) -> str:
    """生成 BMI 可视化条形图"""
    bar_width = 40
    # BMI 范围大致 10-40
    pos = int((bmi - 10) / 30 * bar_width)
    pos = max(0, min(bar_width, pos))

    # 分类区间
    ranges = [
        (0, int((18.5 - 10) / 30 * bar_width), "偏瘦"),
        (int((18.5 - 10) / 30 * bar_width), int((25 - 10) / 30 * bar_width), "正常"),
        (int((25 - 10) / 30 * bar_width), int((30 - 10) / 30 * bar_width), "偏胖"),
        (int((30 - 10) / 30 * bar_width), bar_width, "肥胖"),
    ]

    bar = list("│" + " " * bar_width + "│")
    for start, end, _ in ranges:
        bar[start + 1] = "├"
        bar[end + 1] = "┤" if end < bar_width else "│"
        for i in range(start + 2, end):
            bar[i] = "─"

    bar[pos + 1] = "▲"
    return "".join(bar)


# ── 交互式 REPL ────────────────────────────────────────────
def repl() -> None:
    print("=" * 52)
    print("  纯 Python BMI 计算器 (CLI)")
    print("  输入体重和身高计算 BMI，或使用以下命令：")
    print("  metric <体重kg> <身高m>  - 公制计算")
    print("  imperial <体重lb> <身高in> - 英制计算")
    print("  q                        - 退出")
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

        bmi = None
        height_m = None

        # ── 公制 ──
        if parts[0].lower() == "metric" and len(parts) >= 3:
            try:
                weight = float(parts[1])
                height = float(parts[2])
                bmi = calc_bmi_metric(weight, height)
                height_m = height
            except ValueError as e:
                print(f"  错误：{e}")
                continue

        # ── 英制 ──
        elif parts[0].lower() == "imperial" and len(parts) >= 3:
            try:
                weight = float(parts[1])
                height = float(parts[2])
                bmi = calc_bmi_imperial(weight, height)
                # 转换为公制身高以便计算理想体重
                height_m = height * 0.0254
            except ValueError as e:
                print(f"  错误：{e}")
                continue

        # ── 快捷输入：体重 身高（默认公制，身高单位 cm）──
        elif len(parts) >= 2 and parts[0].replace(".", "").isdigit():
            try:
                weight = float(parts[0])
                height_cm = float(parts[1])
                height_m_val = height_cm / 100
                bmi = calc_bmi_metric(weight, height_m_val)
                height_m = height_m_val
            except ValueError as e:
                print(f"  错误：{e}")
                continue
        else:
            print("  用法：metric <kg> <m> | imperial <lb> <in> | <kg> <cm>")
            continue

        if bmi is not None:
            category, advice = classify(bmi)
            print(f"\n  ┌──────────────────────────────────────┐")
            print(f"  │  BMI: {bmi:.1f}  分类: {category:<12s}  │")
            print(f"  └──────────────────────────────────────┘")
            print(f"  {bmi_bar(bmi)}")
            print(f"  {advice}")

            if height_m is not None:
                low, high = ideal_weight_range(height_m)
                print(f"  您的健康体重范围: {low:.1f} kg ~ {high:.1f} kg")


# ── 命令行入口 ──────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) >= 3:
        try:
            weight = float(sys.argv[1])
            height_cm = float(sys.argv[2])
            height_m = height_cm / 100
            bmi = calc_bmi_metric(weight, height_m)
            category, advice = classify(bmi)
            print(f"BMI: {bmi:.1f} ({category})")
            print(
                f"健康体重范围: {ideal_weight_range(height_m)[0]:.1f} kg ~ {ideal_weight_range(height_m)[1]:.1f} kg"
            )
        except ValueError as e:
            print(f"错误：{e}", file=sys.stderr)
            sys.exit(1)
    else:
        repl()
