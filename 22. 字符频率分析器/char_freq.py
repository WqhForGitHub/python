"""
字符频率分析器
分析文本中各字符的出现频率，
支持 ASCII 可视化、中英文分别统计、频率对比等。
"""

import re
import sys
from collections import Counter

# ── 字符分类 ──────────────────────────────────────────────


def classify_char(ch: str) -> str:
    """对单个字符进行分类。"""
    if re.match(r"[\u4e00-\u9fff]", ch):
        return "中文"
    elif ch.isalpha():
        return "英文"
    elif ch.isdigit():
        return "数字"
    elif ch.isspace():
        return "空白"
    else:
        return "标点"


def get_visible_chars(text: str) -> str:
    """去除空白和控制字符，返回可见字符。"""
    return re.sub(r"\s", "", text)


# ── 频率统计 ──────────────────────────────────────────────


def char_frequency(text: str, case_sensitive: bool = False) -> Counter:
    """统计字符频率。"""
    if not case_sensitive:
        text = text.lower()
    return Counter(text)


def filtered_frequency(
    text: str, filter_type: str = "all", case_sensitive: bool = False
) -> Counter:
    """按类型过滤后统计频率。"""
    if not case_sensitive:
        text = text.lower()

    counter = Counter()
    for ch in text:
        cat = classify_char(ch)
        if filter_type == "all":
            counter[ch] += 1
        elif filter_type == "cn" and cat == "中文":
            counter[ch] += 1
        elif filter_type == "en" and cat == "英文":
            counter[ch] += 1
        elif filter_type == "digit" and cat == "数字":
            counter[ch] += 1
        elif filter_type == "punct" and cat == "标点":
            counter[ch] += 1
        elif filter_type == "visible" and not ch.isspace():
            counter[ch] += 1
    return counter


# ── 结果展示 ──────────────────────────────────────────────


def show_frequency(counter: Counter, top_n: int = 20, title: str = "字符频率") -> None:
    """展示频率统计结果。"""
    total = sum(counter.values())
    if total == 0:
        print("  无数据")
        return

    print(f"\n  ═══ {title} ═══")
    print(f"  {'字符':<6s} {'次数':>6s} {'频率':>8s} {'分布'}")
    print(f"  {'─' * 6} {'─' * 6} {'─' * 8} {'─' * 20}")

    for ch, count in counter.most_common(top_n):
        freq = count / total * 100
        bar = "█" * int(freq * 2)  # 每个█代表0.5%
        display_ch = ch if ch not in (" ", "\n", "\t", "\r") else repr(ch)[1:-1]
        print(f"  {display_ch:<6s} {count:>6d} {freq:>7.2f}% {bar}")

    print()


def show_summary(text: str) -> None:
    """展示文本概要。"""
    total = len(text)
    counter = Counter(text)
    unique = len(counter)

    cats: dict[str, int] = {"中文": 0, "英文": 0, "数字": 0, "空白": 0, "标点": 0}
    for ch in text:
        cats[classify_char(ch)] += 1

    print(f"\n  ═══ 文本概要 ═══")
    print(f"  总字符数：{total:,}")
    print(f"  不同字符：{unique:,}")
    print(f"  ─────────────────────")
    for cat, count in cats.items():
        pct = count / total * 100 if total > 0 else 0
        print(f"  {cat}：{count:,} ({pct:.1f}%)")
    print()


def show_bigram_frequency(text: str, top_n: int = 15) -> None:
    """统计相邻字符对（二元组）频率。"""
    visible = get_visible_chars(text)
    if len(visible) < 2:
        print("  文本太短，无法分析二元组")
        return

    bigrams = Counter()
    for i in range(len(visible) - 1):
        pair = visible[i : i + 2]
        bigrams[pair] += 1

    show_frequency(bigrams, top_n, "相邻字符对频率")


def compare_texts(text1: str, text2: str) -> None:
    """对比两段文本的字符频率。"""
    freq1 = filtered_frequency(text1, "visible")
    freq2 = filtered_frequency(text2, "visible")

    all_chars = set(freq1.keys()) | set(freq2.keys())
    total1 = sum(freq1.values())
    total2 = sum(freq2.values())

    combined = []
    for ch in all_chars:
        p1 = freq1.get(ch, 0) / total1 * 100 if total1 else 0
        p2 = freq2.get(ch, 0) / total2 * 100 if total2 else 0
        combined.append((ch, p1, p2))

    combined.sort(key=lambda x: abs(x[1] - x[2]), reverse=True)

    print(f"\n  ═══ 频率对比 ═══")
    print(f"  {'字符':<6s} {'文本1频率':>10s} {'文本2频率':>10s} {'差异':>8s}")
    print(f"  {'─' * 6} {'─' * 10} {'─' * 10} {'─' * 8}")

    for ch, p1, p2 in combined[:20]:
        display_ch = ch if ch not in (" ", "\n", "\t") else repr(ch)[1:-1]
        diff = p1 - p2
        sign = "+" if diff > 0 else ""
        print(f"  {display_ch:<6s} {p1:>9.2f}% {p2:>9.2f}% {sign}{diff:>7.2f}%")

    print()


# ── 主菜单 ────────────────────────────────────────────────


def print_menu() -> None:
    print("=" * 45)
    print("  字符频率分析器")
    print("=" * 45)
    print("  1. 分析输入文本")
    print("  2. 分析文件")
    print("  3. 中文频率分析")
    print("  4. 英文频率分析")
    print("  5. 相邻字符对分析")
    print("  6. 两段文本频率对比")
    print("  q. 退出")
    print("-" * 45)


def input_text() -> str:
    """多行输入。"""
    print("  请输入文本（空行结束）：")
    lines = []
    while True:
        line = input("  > ")
        if not line:
            break
        lines.append(line)
    return "\n".join(lines)


def read_file(path: str) -> str | None:
    """读取文件。"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"  错误：文件 '{path}' 不存在")
    except Exception as e:
        print(f"  错误：{e}")
    return None


def main() -> None:
    while True:
        print_menu()
        choice = input("  请选择: ").strip()

        if choice == "q":
            print("  再见！")
            break

        elif choice == "1":
            text = input_text()
            if text.strip():
                show_summary(text)
                freq = filtered_frequency(text, "visible")
                show_frequency(freq, top_n=20, title="字符频率")
            else:
                print("  文本为空")

        elif choice == "2":
            path = input("  文件路径: ").strip()
            if path:
                text = read_file(path)
                if text:
                    show_summary(text)
                    freq = filtered_frequency(text, "visible")
                    show_frequency(freq, top_n=20, title="字符频率")

        elif choice == "3":
            text = input_text()
            if text.strip():
                freq = filtered_frequency(text, "cn")
                if freq:
                    show_frequency(freq, top_n=20, title="中文字符频率")
                else:
                    print("  未检测到中文字符")

        elif choice == "4":
            text = input_text()
            if text.strip():
                freq = filtered_frequency(text, "en")
                if freq:
                    show_frequency(freq, top_n=20, title="英文字符频率")
                else:
                    print("  未检测到英文字符")

        elif choice == "5":
            text = input_text()
            if text.strip():
                show_bigram_frequency(text)

        elif choice == "6":
            print("  输入第一段文本：")
            text1 = input_text()
            print("  输入第二段文本：")
            text2 = input_text()
            if text1.strip() and text2.strip():
                compare_texts(text1, text2)

        else:
            print("  无效选择，请重新输入")


if __name__ == "__main__":
    main()
