"""
纯 Python 实现的随机名言生成器（CLI）
支持：随机名言、按分类浏览、按关键词搜索、收藏夹、交互式 REPL
"""

import json
import os
import random
import sys

# ── 名言数据集 ──────────────────────────────────────────────
QUOTES: list[dict[str, str]] = [
    # ── 哲学 ──
    {"text": "我思故我在。", "author": "笛卡尔", "category": "哲学"},
    {"text": "未经审视的人生不值得过。", "author": "苏格拉底", "category": "哲学"},
    {"text": "人是万物的尺度。", "author": "普罗泰戈拉", "category": "哲学"},
    {"text": "存在先于本质。", "author": "萨特", "category": "哲学"},
    {"text": "他人即地狱。", "author": "萨特", "category": "哲学"},
    {"text": "知识就是力量。", "author": "培根", "category": "哲学"},
    {"text": "幸福不在于拥有，而在于存在。", "author": "叔本华", "category": "哲学"},
    # ── 科学 ──
    {"text": "想象力比知识更重要。", "author": "爱因斯坦", "category": "科学"},
    {"text": "在危机中总会诞生机遇。", "author": "爱因斯坦", "category": "科学"},
    {
        "text": "如果我能看得更远，那是因为我站在巨人的肩膀上。",
        "author": "牛顿",
        "category": "科学",
    },
    {"text": "自然界没有飞跃。", "author": "莱布尼茨", "category": "科学"},
    {
        "text": "科学没有国界，因为知识属于全人类。",
        "author": "巴斯德",
        "category": "科学",
    },
    {
        "text": "宇宙不仅比我们想象的奇怪，而且比我们能想象的更奇怪。",
        "author": "霍尔丹",
        "category": "科学",
    },
    # ── 文学 ──
    {
        "text": "生活总是让我们遍体鳞伤，但到后来，那些受伤的地方一定会变成我们最强壮的地方。",
        "author": "海明威",
        "category": "文学",
    },
    {
        "text": "一个人可以被毁灭，但不能被打败。",
        "author": "海明威",
        "category": "文学",
    },
    {
        "text": "所有幸福的家庭都是相似的，每个不幸的家庭各有各的不幸。",
        "author": "托尔斯泰",
        "category": "文学",
    },
    {
        "text": "这是最好的时代，也是最坏的时代。",
        "author": "狄更斯",
        "category": "文学",
    },
    {
        "text": "在过去和未来之间，只有现在这一刻是属于我们的。",
        "author": "普鲁斯特",
        "category": "文学",
    },
    {
        "text": "不要走在我后面，我可能不会引路；不要走在我前面，我可能不会跟随；请走在我的身边，做我的朋友。",
        "author": "加缪",
        "category": "文学",
    },
    # ── 人生 ──
    {"text": "千里之行，始于足下。", "author": "老子", "category": "人生"},
    {"text": "学而不思则罔，思而不学则殆。", "author": "孔子", "category": "人生"},
    {"text": "三军可夺帅也，匹夫不可夺志也。", "author": "孔子", "category": "人生"},
    {
        "text": "天将降大任于斯人也，必先苦其心志，劳其筋骨。",
        "author": "孟子",
        "category": "人生",
    },
    {"text": "路漫漫其修远兮，吾将上下而求索。", "author": "屈原", "category": "人生"},
    {"text": "不以物喜，不以己悲。", "author": "范仲淹", "category": "人生"},
    {
        "text": "天下事有难易乎？为之，则难者亦易矣；不为，则易者亦难矣。",
        "author": "彭端淑",
        "category": "人生",
    },
    # ── 励志 ──
    {
        "text": "你若要喜爱你自己的价值，你就得给世界创造价值。",
        "author": "歌德",
        "category": "励志",
    },
    {"text": "失败乃成功之母。", "author": "谚语", "category": "励志"},
    {"text": "世上无难事，只怕有心人。", "author": "谚语", "category": "励志"},
    {
        "text": "黑夜无论怎样悠长，白昼总会到来。",
        "author": "莎士比亚",
        "category": "励志",
    },
    {
        "text": "伟大不是凭空而来的，伟大是赢得的。",
        "author": "奥巴马",
        "category": "励志",
    },
    {
        "text": "每一个不曾起舞的日子，都是对生命的辜负。",
        "author": "尼采",
        "category": "励志",
    },
    {
        "text": "你必须成为你希望在世界上看到的改变。",
        "author": "甘地",
        "category": "励志",
    },
    {"text": "困难像弹簧，你弱它就强。", "author": "谚语", "category": "励志"},
    # ── 幽默 ──
    {
        "text": "我本可以成为一个无神论者，但我不确定自己是否存在。",
        "author": "佚名",
        "category": "幽默",
    },
    {
        "text": "地球上最丰富的资源就是人类的愚蠢。",
        "author": "爱因斯坦",
        "category": "幽默",
    },
    {
        "text": "世界上最遥远的距离，是我在 if 里，你在 else 里。",
        "author": "程序员",
        "category": "幽默",
    },
    {
        "text": "这个 bug 不是我写的，是之前那个离职的同事写的。",
        "author": "每位程序员",
        "category": "幽默",
    },
    {
        "text": "代码写得好，BUG 自然少；代码写得烂，加班到天亮。",
        "author": "程序员的觉悟",
        "category": "幽默",
    },
    {
        "text": "我没有迟到，是时间早到了。",
        "author": "爱因斯坦（据说）",
        "category": "幽默",
    },
]

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "favorites.json")


# ── 收藏功能 ────────────────────────────────────────────────
def load_favorites() -> list[int]:
    """加载收藏列表"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return []


def save_favorites(favorites: list[int]) -> None:
    """保存收藏列表"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(favorites, f, indent=2, ensure_ascii=False)


# ── 核心功能 ────────────────────────────────────────────────
def get_random_quote() -> dict[str, str]:
    """获取一条随机名言"""
    return random.choice(QUOTES)


def get_quote_by_index(index: int) -> dict[str, str] | None:
    """通过索引获取名言"""
    if 0 <= index < len(QUOTES):
        return QUOTES[index]
    return None


def get_categories() -> list[str]:
    """获取所有分类"""
    return sorted(set(q["category"] for q in QUOTES))


def search_quotes(keyword: str) -> list[tuple[int, dict[str, str]]]:
    """按关键词搜索名言"""
    keyword = keyword.lower()
    results = []
    for i, q in enumerate(QUOTES):
        if keyword in q["text"].lower() or keyword in q["author"].lower():
            results.append((i, q))
    return results


def quotes_by_category(category: str) -> list[tuple[int, dict[str, str]]]:
    """获取某分类下的所有名言"""
    return [(i, q) for i, q in enumerate(QUOTES) if q["category"] == category]


# ── 格式化输出 ──────────────────────────────────────────────
def fmt_quote(
    quote: dict[str, str], index: int | None = None, favorited: bool = False
) -> str:
    """格式化一条名言"""
    star = " ★" if favorited else ""
    idx = f"  [#{index}]" if index is not None else ""
    lines = []
    lines.append(f"  ┌──────────────────────────────────────┐")
    # 自动换行
    text = quote["text"]
    max_width = 36
    if len(text) <= max_width:
        lines.append(f"  │  {text:<36s}  │")
    else:
        # 简单换行
        while text:
            chunk = text[:max_width]
            text = text[max_width:]
            lines.append(f"  │  {chunk:<36s}  │")
    lines.append(f'  │  —— {quote["author"]:<24s}  │')
    lines.append(f'  │  [{quote["category"]}]')
    lines.append(f"  └──────────────────────────────────────┘")
    header = f"  名言{idx}{star}"
    return header + "\n" + "\n".join(lines)


# ── 交互式 REPL ────────────────────────────────────────────
def repl() -> None:
    favorites = load_favorites()

    print("=" * 52)
    print("  纯 Python 随机名言生成器 (CLI)")
    print("  命令：")
    print("  (回车)           - 随机一条名言")
    print("  cat [分类]       - 查看分类/按分类浏览")
    print("  search <关键词>  - 搜索名言")
    print("  #<编号>          - 查看指定编号的名言")
    print("  fav <编号>       - 收藏/取消收藏")
    print("  favs             - 查看收藏列表")
    print("  all              - 列出所有名言")
    print("  q                - 退出")
    print("=" * 52)

    while True:
        try:
            line = input("\n>>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not line:
            # 直接回车：随机名言
            quote = get_random_quote()
            index = QUOTES.index(quote)
            print(fmt_quote(quote, index, index in favorites))
            continue

        parts = line.split()
        cmd = parts[0]

        if cmd.lower() == "q":
            print("再见！")
            break

        # ── 分类 ──
        if cmd.lower() == "cat":
            if len(parts) >= 2:
                category = parts[1]
                results = quotes_by_category(category)
                if results:
                    for i, q in results:
                        print(fmt_quote(q, i, i in favorites))
                    print(f"\n  [{category}] 共 {len(results)} 条")
                else:
                    print(f"  分类 '{category}' 不存在")
                    print(f"  可用分类：{', '.join(get_categories())}")
            else:
                cats = get_categories()
                print("\n  可用分类：")
                for c in cats:
                    count = len(quotes_by_category(c))
                    print(f"    {c} ({count} 条)")
            continue

        # ── 搜索 ──
        if cmd.lower() == "search" and len(parts) >= 2:
            keyword = " ".join(parts[1:])
            results = search_quotes(keyword)
            if results:
                for i, q in results:
                    print(fmt_quote(q, i, i in favorites))
                print(f"\n  搜索 '{keyword}' 找到 {len(results)} 条")
            else:
                print(f"  未找到包含 '{keyword}' 的名言")
            continue

        # ── 编号查看 ──
        if cmd.startswith("#") and len(cmd) > 1:
            try:
                index = int(cmd[1:])
                quote = get_quote_by_index(index)
                if quote:
                    print(fmt_quote(quote, index, index in favorites))
                else:
                    print(f"  编号 #{index} 不存在（范围 0-{len(QUOTES)-1}）")
            except ValueError:
                print("  错误：请输入有效编号，如 #0")
            continue

        # ── 收藏 ──
        if cmd.lower() == "fav" and len(parts) >= 2:
            try:
                index = int(parts[1])
                if 0 <= index < len(QUOTES):
                    if index in favorites:
                        favorites.remove(index)
                        print(f"  已取消收藏 #{index}")
                    else:
                        favorites.append(index)
                        print(f"  已收藏 #{index}")
                    save_favorites(favorites)
                else:
                    print(f"  编号 #{index} 不存在（范围 0-{len(QUOTES)-1}）")
            except ValueError:
                print("  错误：请输入有效编号，如 fav 0")
            continue

        # ── 收藏列表 ──
        if cmd.lower() == "favs":
            if favorites:
                for i in favorites:
                    if i < len(QUOTES):
                        print(fmt_quote(QUOTES[i], i, True))
                print(f"\n  收藏夹共 {len(favorites)} 条")
            else:
                print("  收藏夹为空")
            continue

        # ── 列出所有 ──
        if cmd.lower() == "all":
            for i, q in enumerate(QUOTES):
                star = " ★" if i in favorites else ""
                print(
                    f"  [{i:>2d}]{star} {q['text'][:30]}... —— {q['author']}  [{q['category']}]"
                )
            print(f"\n  共 {len(QUOTES)} 条名言")
            continue

        print("  未知命令。按回车获取随机名言，输入 q 退出")


# ── 命令行入口 ──────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "random":
            quote = get_random_quote()
            print(f'{quote["text"]} —— {quote["author"]}')
        elif arg == "search" and len(sys.argv) >= 3:
            keyword = " ".join(sys.argv[2:])
            results = search_quotes(keyword)
            for i, q in results:
                print(f'[{i}] {q["text"]} —— {q["author"]}  [{q["category"]}]')
            if not results:
                print(f"未找到包含 '{keyword}' 的名言")
        elif arg.isdigit():
            index = int(arg)
            quote = get_quote_by_index(index)
            if quote:
                print(f'{quote["text"]} —— {quote["author"]}  [{quote["category"]}]')
            else:
                print(f"编号 {index} 不存在", file=sys.stderr)
                sys.exit(1)
        else:
            print(
                f"用法: python quote.py [random | search <keyword> | <index>]",
                file=sys.stderr,
            )
            sys.exit(1)
    else:
        repl()
