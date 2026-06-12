#!/usr/bin/env python3
"""
纯 Python 实现的回文检测器（CLI）
支持：字符串回文检测、数字回文检测、文件批量检测、交互式模式
"""

import argparse
import re
import sys


# ── 回文检测核心 ───────────────────────────────────────────
def is_palindrome(
    text: str,
    ignore_case: bool = True,
    ignore_spaces: bool = True,
    ignore_punctuation: bool = True,
) -> bool:
    """
    检测字符串是否为回文

    Args:
        text: 待检测文本
        ignore_case: 忽略大小写
        ignore_spaces: 忽略空格
        ignore_punctuation: 忽略标点符号

    Returns:
        是否为回文
    """
    processed = text

    if ignore_case:
        processed = processed.lower()

    if ignore_spaces:
        processed = processed.replace(" ", "")

    if ignore_punctuation:
        # 去除所有非字母数字字符（保留 Unicode 字母和数字）
        processed = re.sub(r"[^\w]", "", processed, flags=re.UNICODE)

    # 双指针检测
    left, right = 0, len(processed) - 1
    while left < right:
        if processed[left] != processed[right]:
            return False
        left += 1
        right -= 1

    return True


def is_numeric_palindrome(number: int) -> bool:
    """
    检测整数是否为回文数字（不转换为字符串）

    使用数学方法反转数字
    """
    if number < 0:
        return False
    if number < 10:
        return True
    if number % 10 == 0:
        return False

    reversed_half = 0
    original = number

    while number > reversed_half:
        reversed_half = reversed_half * 10 + number % 10
        number //= 10

    # 偶数位：number == reversed_half
    # 奇数位：number == reversed_half // 10
    return number == reversed_half or number == reversed_half // 10


# ── 回文分析 ───────────────────────────────────────────────
def analyze_palindrome(text: str) -> dict:
    """
    对文本进行回文分析，返回详细信息

    Returns:
        包含分析结果的字典
    """
    # 原始检测
    is_strict = is_palindrome(
        text,
        ignore_case=False,
        ignore_spaces=False,
        ignore_punctuation=False,
    )
    is_loose = is_palindrome(
        text,
        ignore_case=True,
        ignore_spaces=True,
        ignore_punctuation=True,
    )

    # 清理后的文本
    cleaned = re.sub(r"[^\w]", "", text, flags=re.UNICODE).replace(" ", "").lower()

    # 找最长回文子串
    longest = longest_palindromic_substring(cleaned) if cleaned else ""

    return {
        "text": text,
        "cleaned": cleaned,
        "is_strict_palindrome": is_strict,
        "is_loose_palindrome": is_loose,
        "longest_palindromic_substring": longest,
        "length": len(text),
        "cleaned_length": len(cleaned),
    }


def longest_palindromic_substring(text: str) -> str:
    """
    使用中心扩展法找最长回文子串

    时间复杂度: O(n^2)
    空间复杂度: O(1)
    """
    if not text:
        return ""

    start, max_len = 0, 1

    for i in range(len(text)):
        # 奇数长度回文
        len1 = _expand_around_center(text, i, i)
        # 偶数长度回文
        len2 = _expand_around_center(text, i, i + 1)

        length = max(len1, len2)
        if length > max_len:
            max_len = length
            start = i - (length - 1) // 2

    return text[start : start + max_len]


def _expand_around_center(text: str, left: int, right: int) -> int:
    """从中心向两边扩展，返回回文长度"""
    while left >= 0 and right < len(text) and text[left] == text[right]:
        left -= 1
        right += 1
    return right - left - 1


# ── 输出格式化 ─────────────────────────────────────────────
def print_result(result: dict) -> None:
    """格式化输出回文分析结果"""
    text = result["text"]
    if len(text) > 40:
        display_text = text[:37] + "..."
    else:
        display_text = text

    print(f"\n  文本: {display_text}")
    print(f"  长度: {result['length']} (清理后: {result['cleaned_length']})")

    # 严格模式
    strict_icon = "✓" if result["is_strict_palindrome"] else "✗"
    strict_text = "是回文" if result["is_strict_palindrome"] else "不是回文"
    print(f"  严格检测 (区分大小写/空格/标点): {strict_icon} {strict_text}")

    # 宽松模式
    loose_icon = "✓" if result["is_loose_palindrome"] else "✗"
    loose_text = "是回文" if result["is_loose_palindrome"] else "不是回文"
    print(f"  宽松检测 (忽略大小写/空格/标点): {loose_icon} {loose_text}")

    # 最长回文子串
    longest = result["longest_palindromic_substring"]
    if longest:
        print(f'  最长回文子串: "{longest}" (长度 {len(longest)})')


# ── 文件批量检测 ──────────────────────────────────────────
def check_file(filepath: str) -> None:
    """从文件中逐行读取文本进行回文检测"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"  错误: 文件 '{filepath}' 不存在。")
        return
    except IOError as e:
        print(f"  错误: 无法读取文件 - {e}")
        return

    print(f"\n  从文件 '{filepath}' 读取 {len(lines)} 行:")
    print("  " + "-" * 44)

    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        result = analyze_palindrome(line)
        status = "回文" if result["is_loose_palindrome"] else "非回文"
        display = line[:30] + "..." if len(line) > 30 else line
        print(f"  {i:>3}. {display:<33} [{status}]")

    print("  " + "-" * 44)


# ── 交互式模式 ─────────────────────────────────────────────
def interactive_mode() -> None:
    """交互式回文检测"""
    print("=" * 48)
    print("  纯 Python 回文检测器 (CLI)")
    print("  输入文本检测是否为回文，输入 q 退出")
    print("=" * 48)

    while True:
        try:
            text = input("\n>>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  再见！")
            break

        if not text:
            continue
        if text.lower() == "q":
            print("  再见！")
            break

        # 检测是否为纯数字
        if text.lstrip("-").isdigit():
            number = int(text)
            num_result = is_numeric_palindrome(number)
            num_icon = "✓" if num_result else "✗"
            num_text = "是回文数字" if num_result else "不是回文数字"
            print(f"  数字检测: {num_icon} {number} {num_text}")

        # 字符串检测
        result = analyze_palindrome(text)
        print_result(result)


# ── 命令行入口 ─────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        prog="palindrome",
        description="纯 Python 回文检测器 - 检测文本/数字是否为回文",
    )
    parser.add_argument(
        "text",
        nargs="*",
        help="待检测的文本",
    )
    parser.add_argument(
        "-f",
        "--file",
        help="从文件中读取文本进行批量检测",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="严格模式 (区分大小写/空格/标点)",
    )
    parser.add_argument(
        "-n",
        "--number",
        type=int,
        help="检测数字是否为回文",
    )

    # 无参数时进入交互模式
    if len(sys.argv) == 1:
        interactive_mode()
        return

    args = parser.parse_args()

    # 文件模式
    if args.file:
        check_file(args.file)
        return

    # 数字模式
    if args.number is not None:
        result = is_numeric_palindrome(args.number)
        icon = "✓" if result else "✗"
        text = "是回文数字" if result else "不是回文数字"
        print(f"  {icon} {args.number} {text}")
        return

    # 文本模式
    if args.text:
        text = " ".join(args.text)
        if args.strict:
            result = is_palindrome(
                text,
                ignore_case=False,
                ignore_spaces=False,
                ignore_punctuation=False,
            )
            icon = "✓" if result else "✗"
            status = "是回文" if result else "不是回文"
            print(f'  {icon} "{text}" {status} (严格模式)')
        else:
            analysis = analyze_palindrome(text)
            print_result(analysis)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
