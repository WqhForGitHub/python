"""
拼写检查器（字典匹配）
功能：
    - 基于词典的英文拼写检查
    - 未命中单词 -> 给出建议（基于编辑距离）
    - 编辑距离使用 Levenshtein 算法（DP 实现）
    - 候选过滤：仅返回距离 <= max_dist 的词，按频率/距离排序
    - 支持自定义词典与添加词
    - 提供文本批量检查接口（保留位置信息）
"""

import re
from collections import Counter


# 内置小词典 + 词频
BUILTIN_VOCAB = {
    "the": 100, "be": 90, "to": 88, "of": 80, "and": 75, "a": 70, "in": 68,
    "that": 60, "have": 55, "i": 90, "it": 50, "for": 48, "not": 45, "on": 42,
    "with": 40, "he": 38, "as": 36, "you": 35, "do": 33, "at": 32,
    "this": 30, "but": 28, "his": 27, "by": 26, "from": 25, "they": 24,
    "we": 23, "say": 22, "her": 21, "she": 20, "or": 19, "an": 18,
    "will": 17, "my": 16, "one": 15, "all": 14, "would": 13, "there": 12,
    "their": 11, "what": 10, "so": 9, "up": 8, "out": 7, "if": 6,
    "about": 5, "who": 4, "get": 3, "which": 2, "go": 2, "me": 2,
    "hello": 30, "world": 30, "python": 50, "spell": 20, "check": 25,
    "checker": 18, "dictionary": 15, "language": 14, "computer": 13,
    "program": 20, "programming": 18, "function": 12, "variable": 10,
    "object": 11, "class": 10, "method": 9, "string": 12, "integer": 8,
    "number": 12, "result": 10, "example": 14, "demo": 12, "code": 15,
    "test": 16, "data": 18, "file": 17, "system": 14, "value": 11,
    "name": 16, "good": 14, "great": 11, "fast": 9, "slow": 6,
    "love": 11, "like": 13, "happy": 9, "today": 10, "tomorrow": 7,
    "morning": 8, "night": 7, "year": 9, "time": 12, "make": 11,
    "take": 10, "see": 9, "know": 11, "think": 10,
}


def levenshtein(a: str, b: str) -> int:
    """计算编辑距离（DP）"""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            cur[j] = min(
                cur[j - 1] + 1,        # 插入
                prev[j] + 1,           # 删除
                prev[j - 1] + cost,    # 替换
            )
        prev = cur
    return prev[-1]


class SpellChecker:
    def __init__(self, vocab: dict = None):
        self.vocab = Counter(vocab or BUILTIN_VOCAB)

    def add_word(self, word: str, freq: int = 1):
        self.vocab[word.lower()] += freq

    def is_correct(self, word: str) -> bool:
        return word.lower() in self.vocab

    def suggest(self, word: str, max_dist: int = 2, top: int = 5) -> list:
        """返回候选列表 [(word, dist, freq)]"""
        w = word.lower()
        if w in self.vocab:
            return [(w, 0, self.vocab[w])]
        candidates = []
        for vocab_w, freq in self.vocab.items():
            # 长度差太大就不算了，提速
            if abs(len(vocab_w) - len(w)) > max_dist:
                continue
            d = levenshtein(w, vocab_w)
            if d <= max_dist:
                candidates.append((vocab_w, d, freq))
        # 按 (距离升序, 频率降序) 排
        candidates.sort(key=lambda x: (x[1], -x[2]))
        return candidates[:top]

    def check_text(self, text: str, max_dist: int = 2) -> list:
        """检查整段文本，返回每个错词的位置与建议
        返回: [{'word','start','end','suggestions':[(w,dist,freq)]}, ...]
        """
        result = []
        for m in re.finditer(r"[A-Za-z']+", text):
            w = m.group(0)
            if self.is_correct(w):
                continue
            sugg = self.suggest(w, max_dist=max_dist)
            result.append({
                "word": w, "start": m.start(), "end": m.end(),
                "suggestions": sugg,
            })
        return result


# ==================== Demo ====================

def underline_errors(text: str, errors: list) -> str:
    """在原文下用 ^^^^ 标记拼错的位置"""
    if not errors:
        return text
    line = list(" " * len(text))
    for e in errors:
        for i in range(e["start"], e["end"]):
            line[i] = "^"
    return text + "\n" + "".join(line)


if __name__ == "__main__":
    print("=" * 60)
    print("  拼写检查器（字典匹配） Demo")
    print("=" * 60)

    sc = SpellChecker()

    # 1. 单词检查
    print("\n--- 1. 单词级检查 ---")
    samples = ["python", "pythn", "helo", "computor", "progrmming", "love", "luv"]
    for w in samples:
        if sc.is_correct(w):
            print(f"  [OK]   {w}")
        else:
            sugg = sc.suggest(w)
            cands = ", ".join(f"{s[0]}(d={s[1]})" for s in sugg)
            print(f"  [ERR]  {w}  -> 建议: {cands}")

    # 2. 文本检查
    print("\n--- 2. 整段文本检查 ---")
    text = "Helo wrld, I luv pythn progrmming and writting code."
    errors = sc.check_text(text)
    print(underline_errors(text, errors))
    print()
    for e in errors:
        cands = ", ".join(f"{s[0]}(d={s[1]})" for s in e["suggestions"])
        print(f"  位置 {e['start']:>3}: '{e['word']}' -> {cands or '无建议'}")

    # 3. 添加自定义词
    print("\n--- 3. 自定义词典 ---")
    sc.add_word("luv", 5)
    sc.add_word("writting", 3)
    print(f"  添加 'luv' 与 'writting' 后再检查同样文本：")
    errors2 = sc.check_text(text)
    print(f"  错词数: {len(errors2)} -> {[e['word'] for e in errors2]}")

    # 4. 编辑距离展示
    print("\n--- 4. 编辑距离演示 ---")
    pairs = [("kitten", "sitting"), ("flaw", "lawn"), ("python", "pyhton")]
    for a, b in pairs:
        print(f"  '{a}' <-> '{b}'  距离={levenshtein(a, b)}")

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
