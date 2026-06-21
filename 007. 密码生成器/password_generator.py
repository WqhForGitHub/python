#!/usr/bin/env python3
"""
纯 Python 实现的密码生成器（CLI）
支持：自定义长度、字符集选择、密码强度评估、批量生成
"""

import argparse
import random
import string
import sys

# ── 字符集定义 ─────────────────────────────────────────────
CHARSET = {
    "lower": string.ascii_lowercase,  # a-z
    "upper": string.ascii_uppercase,  # A-Z
    "digits": string.digits,  # 0-9
    "symbols": "!@#$%^&*()_+-=[]{}|;:,.<>?",  # 特殊符号
}

# 排除容易混淆的字符
CHARSET_SAFE = {
    "lower": "abcdefghjkmnpqrstuvwxyz",  # 去掉 i, l, o
    "upper": "ABCDEFGHJKMNPQRSTUVWXYZ",  # 去掉 I, L, O
    "digits": "23456789",  # 去掉 0, 1
    "symbols": "!@#$%^&*_+-=?",  # 去掉容易混淆的符号
}


# ── 密码生成 ───────────────────────────────────────────────
def generate_password(
    length: int = 16,
    use_lower: bool = True,
    use_upper: bool = True,
    use_digits: bool = True,
    use_symbols: bool = True,
    exclude_ambiguous: bool = False,
) -> str:
    """
    生成随机密码

    Args:
        length: 密码长度
        use_lower: 包含小写字母
        use_upper: 包含大写字母
        use_digits: 包含数字
        use_symbols: 包含特殊符号
        exclude_ambiguous: 排除容易混淆的字符

    Returns:
        生成的密码字符串
    """
    if length < 1:
        raise ValueError("密码长度至少为 1")

    charset_map = CHARSET_SAFE if exclude_ambiguous else CHARSET

    # 构建字符池
    pool = ""
    required_chars = []

    if use_lower:
        pool += charset_map["lower"]
        required_chars.append(random.choice(charset_map["lower"]))
    if use_upper:
        pool += charset_map["upper"]
        required_chars.append(random.choice(charset_map["upper"]))
    if use_digits:
        pool += charset_map["digits"]
        required_chars.append(random.choice(charset_map["digits"]))
    if use_symbols:
        pool += charset_map["symbols"]
        required_chars.append(random.choice(charset_map["symbols"]))

    if not pool:
        raise ValueError("至少需要选择一种字符类型")

    # 确保每种选中的字符类型至少出现一次
    if length < len(required_chars):
        raise ValueError(
            f"密码长度 {length} 太短，至少需要 {len(required_chars)} 位"
            f"以包含所有选中的字符类型"
        )

    # 填充剩余长度
    remaining = length - len(required_chars)
    password_chars = required_chars + [random.choice(pool) for _ in range(remaining)]

    # 打乱顺序
    random.shuffle(password_chars)
    return "".join(password_chars)


# ── 密码强度评估 ──────────────────────────────────────────
def evaluate_strength(password: str) -> tuple[str, int, list[str]]:
    """
    评估密码强度

    Returns:
        (等级名称, 分数 0-100, 建议列表)
    """
    score = 0
    suggestions = []

    # 长度评分
    length = len(password)
    if length >= 16:
        score += 30
    elif length >= 12:
        score += 25
    elif length >= 8:
        score += 15
    elif length >= 6:
        score += 8
    else:
        score += 3
        suggestions.append("建议密码长度至少 8 位")

    # 字符类型多样性
    has_lower = any(c in string.ascii_lowercase for c in password)
    has_upper = any(c in string.ascii_uppercase for c in password)
    has_digit = any(c in string.digits for c in password)
    has_symbol = any(c in CHARSET["symbols"] for c in password)

    diversity = sum([has_lower, has_upper, has_digit, has_symbol])
    score += diversity * 15

    if not has_lower:
        suggestions.append("建议添加小写字母")
    if not has_upper:
        suggestions.append("建议添加大写字母")
    if not has_digit:
        suggestions.append("建议添加数字")
    if not has_symbol:
        suggestions.append("建议添加特殊符号")

    # 重复字符惩罚
    unique_ratio = len(set(password)) / max(length, 1)
    if unique_ratio < 0.5:
        score -= 10
        suggestions.append("密码中重复字符过多")

    # 连续字符惩罚
    consecutive = 0
    for i in range(1, length):
        if abs(ord(password[i]) - ord(password[i - 1])) == 1:
            consecutive += 1
    if consecutive > 2:
        score -= 10
        suggestions.append("避免连续字符（如 abc、123）")

    # 限制分数范围
    score = max(0, min(100, score))

    # 等级
    if score >= 80:
        level = "强"
    elif score >= 60:
        level = "中等"
    elif score >= 40:
        level = "弱"
    else:
        level = "非常弱"

    return level, score, suggestions


# ── 密码强度条 ────────────────────────────────────────────
def strength_bar(score: int) -> str:
    """生成分数可视化条"""
    bar_length = 20
    filled = int(bar_length * score / 100)
    if score >= 80:
        symbol = "█"
    elif score >= 60:
        symbol = "▓"
    elif score >= 40:
        symbol = "▒"
    else:
        symbol = "░"
    return f"[{symbol * filled}{'░' * (bar_length - filled)}] {score}/100"


# ── 交互式模式 ─────────────────────────────────────────────
def interactive_mode() -> None:
    """交互式生成密码"""
    print("=" * 48)
    print("  纯 Python 密码生成器 (CLI)")
    print("  生成安全随机密码")
    print("=" * 48)

    while True:
        try:
            length_input = input("\n  密码长度 (默认 16): ").strip()
            length = int(length_input) if length_input else 16
        except ValueError:
            print("  错误：请输入有效的整数。")
            continue
        except (EOFError, KeyboardInterrupt):
            print("\n  再见！")
            break

        print("  字符类型 (y/n):")
        try:
            use_lower = input("    小写字母 (默认 y): ").strip().lower() != "n"
            use_upper = input("    大写字母 (默认 y): ").strip().lower() != "n"
            use_digits = input("    数字 (默认 y): ").strip().lower() != "n"
            use_symbols = input("    特殊符号 (默认 y): ").strip().lower() != "n"
            exclude_ambiguous = (
                input("    排除易混淆字符 (默认 n): ").strip().lower() == "y"
            )
        except (EOFError, KeyboardInterrupt):
            print("\n  再见！")
            break

        try:
            count_input = input("  生成数量 (默认 1): ").strip()
            count = int(count_input) if count_input else 1
        except ValueError:
            count = 1
        except (EOFError, KeyboardInterrupt):
            print("\n  再见！")
            break

        print()
        try:
            for i in range(count):
                password = generate_password(
                    length=length,
                    use_lower=use_lower,
                    use_upper=use_upper,
                    use_digits=use_digits,
                    use_symbols=use_symbols,
                    exclude_ambiguous=exclude_ambiguous,
                )
                level, score, _ = evaluate_strength(password)
                print(f"  {i + 1}. {password}")
                print(f"     强度: {level}  {strength_bar(score)}")
        except ValueError as e:
            print(f"  错误：{e}")
            continue

        try:
            again = input("\n  继续生成? (Y/n): ").strip().lower()
            if again == "n":
                print("  再见！")
                break
        except (EOFError, KeyboardInterrupt):
            print("\n  再见！")
            break


# ── 命令行入口 ─────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        prog="password_generator",
        description="纯 Python 密码生成器 - 生成安全随机密码",
    )
    parser.add_argument(
        "-n",
        "--length",
        type=int,
        default=16,
        help="密码长度 (默认 16)",
    )
    parser.add_argument(
        "-c",
        "--count",
        type=int,
        default=1,
        help="生成数量 (默认 1)",
    )
    parser.add_argument(
        "--no-lower",
        action="store_true",
        help="不包含小写字母",
    )
    parser.add_argument(
        "--no-upper",
        action="store_true",
        help="不包含大写字母",
    )
    parser.add_argument(
        "--no-digits",
        action="store_true",
        help="不包含数字",
    )
    parser.add_argument(
        "--no-symbols",
        action="store_true",
        help="不包含特殊符号",
    )
    parser.add_argument(
        "--exclude-ambiguous",
        action="store_true",
        help="排除容易混淆的字符 (0/O, 1/I/l 等)",
    )
    parser.add_argument(
        "--evaluate",
        type=str,
        metavar="PASSWORD",
        help="评估指定密码的强度",
    )

    # 无参数时进入交互模式
    if len(sys.argv) == 1:
        interactive_mode()
        return

    args = parser.parse_args()

    # 评估模式
    if args.evaluate:
        level, score, suggestions = evaluate_strength(args.evaluate)
        print(f"  密码: {'*' * len(args.evaluate)}")
        print(f"  强度: {level}  {strength_bar(score)}")
        if suggestions:
            print("  建议:")
            for s in suggestions:
                print(f"    - {s}")
        return

    # 生成模式
    try:
        for i in range(args.count):
            password = generate_password(
                length=args.length,
                use_lower=not args.no_lower,
                use_upper=not args.no_upper,
                use_digits=not args.no_digits,
                use_symbols=not args.no_symbols,
                exclude_ambiguous=args.exclude_ambiguous,
            )
            level, score, _ = evaluate_strength(password)
            if args.count > 1:
                print(f"{i + 1}. {password}  [{level} {score}/100]")
            else:
                print(password)
                print(f"  强度: {level}  {strength_bar(score)}")
    except ValueError as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
