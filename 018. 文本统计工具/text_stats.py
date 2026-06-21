"""
文本统计工具
统计文本的字符数、单词数、句子数、段落数，
显示词频排行、平均词长、阅读时长等。
"""

import re
import sys

# ── 正则定义 ──────────────────────────────────────────────

WORD_PATTERN = re.compile(r"[a-zA-Z\u4e00-\u9fff]+")
CN_CHAR_PATTERN = re.compile(r"[\u4e00-\u9fff]")
SENTENCE_PATTERN = re.compile(r"[。！？.!?]+")
PARA_PATTERN = re.compile(r"\n\s*\n")

# ── 统计逻辑 ──────────────────────────────────────────────


def count_chars(text: str) -> dict[str, int]:
    """统计各类字符数量。"""
    total = len(text)
    no_space = len(text.replace(" ", "").replace("\t", "").replace("\n", ""))
    cn_chars = len(CN_CHAR_PATTERN.findall(text))
    en_chars = len(re.findall(r"[a-zA-Z]", text))
    digits = len(re.findall(r"\d", text))
    punctuation = len(re.findall(r"[^\w\s]", text, re.UNICODE))
    spaces = total - no_space
    return {
        "总字符": total,
        "非空白字符": no_space,
        "中文字符": cn_chars,
        "英文字母": en_chars,
        "数字": digits,
        "标点符号": punctuation,
        "空白字符": spaces,
    }


def count_words(text: str) -> int:
    """统计单词/词语数量。中文按字计词，英文按空格分词。"""
    cn_chars = len(CN_CHAR_PATTERN.findall(text))
    en_words = len(re.findall(r"[a-zA-Z]+", text))
    return cn_chars + en_words


def count_sentences(text: str) -> int:
    """统计句子数量。"""
    matches = SENTENCE_PATTERN.findall(text)
    return len(matches) if matches else (1 if text.strip() else 0)


def count_paragraphs(text: str) -> int:
    """统计段落数量。"""
    paras = PARA_PATTERN.split(text.strip())
    return len([p for p in paras if p.strip()])


def word_frequency(text: str, top_n: int = 10) -> list[tuple[str, int]]:
    """统计词频，返回前 N 个。"""
    # 中文按单字统计
    cn_chars = CN_CHAR_PATTERN.findall(text)
    # 英文按单词统计（转小写）
    en_words = [w.lower() for w in re.findall(r"[a-zA-Z]+", text)]

    freq: dict[str, int] = {}
    for ch in cn_chars:
        freq[ch] = freq.get(ch, 0) + 1
    for w in en_words:
        freq[w] = freq.get(w, 0) + 1

    sorted_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return sorted_freq[:top_n]


def avg_word_length(text: str) -> float:
    """计算英文平均词长。"""
    en_words = re.findall(r"[a-zA-Z]+", text)
    if not en_words:
        return 0.0
    return sum(len(w) for w in en_words) / len(en_words)


def reading_time(text: str, wpm: int = 300) -> int:
    """估算阅读时长（分钟），中文约 300 字/分钟，英文约 300 词/分钟。"""
    words = count_words(text)
    minutes = max(1, round(words / wpm))
    return minutes


def line_stats(text: str) -> dict[str, int]:
    """统计行数信息。"""
    lines = text.split("\n")
    total = len(lines)
    non_empty = len([l for l in lines if l.strip()])
    return {"总行数": total, "非空行": non_empty, "空行": total - non_empty}


# ── 结果展示 ──────────────────────────────────────────────


def show_stats(text: str) -> None:
    """展示完整的文本统计信息。"""
    if not text.strip():
        print("  文本为空，无法统计")
        return

    chars = count_chars(text)
    words = count_words(text)
    sentences = count_sentences(text)
    paragraphs = count_paragraphs(text)
    lines = line_stats(text)
    avg_len = avg_word_length(text)
    read_min = reading_time(text)
    freq = word_frequency(text)

    print("\n  ═══ 文本统计结果 ═══")
    print(f"  ── 字符统计 ──")
    for k, v in chars.items():
        print(f"  {k:　<6s}：{v:,}")

    print(f"  ── 其他统计 ──")
    print(f"  词语/字数：{words:,}")
    print(f"  句子数　：{sentences:,}")
    print(f"  段落数　：{paragraphs:,}")
    print(
        f"  总行数　：{lines['总行数']:,}  非空行：{lines['非空行']:,}  空行：{lines['空行']:,}"
    )
    print(f"  英文均词长：{avg_len:.1f} 个字母")
    print(f"  预计阅读　：{read_min} 分钟")

    if freq:
        print(f"  ── 词频 TOP {min(len(freq), 10)} ──")
        for word, count in freq:
            bar = "█" * min(count, 30)
            print(f"  {word:>6s} {count:>4d} {bar}")

    print()


# ── 主菜单 ────────────────────────────────────────────────


def print_menu() -> None:
    print("=" * 45)
    print("  文本统计工具")
    print("=" * 45)
    print("  1. 输入文本进行统计")
    print("  2. 从文件读取并统计")
    print("  3. 统计剪贴板文本")
    print("  q. 退出")
    print("-" * 45)


def input_text() -> str:
    """多行输入文本。"""
    print("  请输入文本（输入空行结束）：")
    lines = []
    while True:
        line = input("  > ")
        if not line:
            break
        lines.append(line)
    return "\n".join(lines)


def read_file(path: str) -> str | None:
    """读取文件内容。"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"  错误：文件 '{path}' 不存在")
    except PermissionError:
        print(f"  错误：无权限读取文件 '{path}'")
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
            show_stats(text)

        elif choice == "2":
            path = input("  请输入文件路径: ").strip()
            if path:
                text = read_file(path)
                if text is not None:
                    show_stats(text)

        elif choice == "3":
            try:
                import subprocess

                result = subprocess.run(
                    ["powershell", "-command", "Get-Clipboard"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                text = result.stdout.strip()
                if text:
                    print(f"  已获取剪贴板文本（{len(text)} 字符）")
                    show_stats(text)
                else:
                    print("  剪贴板为空")
            except Exception:
                print("  无法访问剪贴板")

        else:
            print("  无效选择，请重新输入")


if __name__ == "__main__":
    main()
