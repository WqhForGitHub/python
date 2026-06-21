# -*- coding: utf-8 -*-
"""
词法分析器 (Lexer)
- 通用化的词法分析器：基于规则配置驱动
- 支持：标识符、关键字、数字（整数/浮点/十六进制）、字符串（含转义）、
       运算符、标点符号、单/多行注释
- 输出 Token 流，记录行列信息
- 提供命令行工具：可对任意源文件输出 token 列表

用法：
    python lexer.py samples/demo.src
"""
import os
import re
import sys
from dataclasses import dataclass, field


@dataclass
class Token:
    type: str
    value: object
    line: int
    col: int

    def __str__(self):
        return f"{self.line:>3}:{self.col:<3}  {self.type:<10}  {self.value!r}"


class LexerError(Exception):
    pass


# ---------- 默认规则 ----------
DEFAULT_KEYWORDS = {
    "if", "else", "while", "for", "do", "return", "break", "continue",
    "let", "const", "fn", "true", "false", "null", "and", "or", "not",
    "import", "export", "class", "new",
}

# 顺序优先：先长后短，先具体后通用；注释要在 OP 之前
DEFAULT_RULES = [
    ("WHITESPACE",  r"[ \t\r]+"),
    ("NEWLINE",     r"\n"),
    ("LINE_COMMENT", r"//[^\n]*"),
    ("BLOCK_COMMENT", r"/\*[\s\S]*?\*/"),
    ("HEX",         r"0[xX][0-9a-fA-F]+"),
    ("FLOAT",       r"\d+\.\d+([eE][+-]?\d+)?|\d+[eE][+-]?\d+"),
    ("INT",         r"\d+"),
    ("STRING",      r'"([^"\\\n]|\\.)*"'),
    ("CHAR",        r"'([^'\\\n]|\\.)'"),
    ("IDENT",       r"[A-Za-z_][A-Za-z_0-9]*"),
    # 多字符运算符放前面
    ("OP",          r"==|!=|<=|>=|&&|\|\||\+\+|--|\+=|-=|\*=|/=|->|=>|::|\.\.|"
                    r"[+\-*/%=<>!&|^~?:.,;(){}\[\]]"),
]


class Lexer:
    def __init__(self, source, keywords=None, rules=None, filename="<source>"):
        self.source = source
        self.filename = filename
        self.keywords = set(keywords) if keywords is not None else DEFAULT_KEYWORDS
        self.rules = rules if rules is not None else DEFAULT_RULES
        self._regex = re.compile(
            "|".join(f"(?P<{name}>{pat})" for name, pat in self.rules)
        )

    def tokenize(self):
        tokens = []
        line = 1
        col = 1
        pos = 0
        src = self.source
        n = len(src)

        while pos < n:
            m = self._regex.match(src, pos)
            if not m:
                raise LexerError(f"{self.filename}:{line}:{col} 非法字符 {src[pos]!r}")
            kind = m.lastgroup
            value = m.group()

            # 计算行列
            tok_line, tok_col = line, col
            newlines = value.count("\n")
            if newlines:
                line += newlines
                col = len(value) - value.rfind("\n")
            else:
                col += len(value)
            pos = m.end()

            if kind in ("WHITESPACE", "NEWLINE", "LINE_COMMENT", "BLOCK_COMMENT"):
                continue

            if kind == "INT":
                value = int(value)
            elif kind == "HEX":
                value = int(value, 16)
                kind = "INT"
            elif kind == "FLOAT":
                value = float(value)
            elif kind == "STRING":
                value = bytes(value[1:-1], "utf-8").decode("unicode_escape")
            elif kind == "CHAR":
                value = bytes(value[1:-1], "utf-8").decode("unicode_escape")
            elif kind == "IDENT":
                if value in self.keywords:
                    kind = "KEYWORD"

            tokens.append(Token(kind, value, tok_line, tok_col))

        tokens.append(Token("EOF", None, line, col))
        return tokens


def main():
    if len(sys.argv) < 2:
        # 简单交互
        print("Lexer Demo (no file given). 输入源代码，Ctrl+D / Ctrl+Z 结束:")
        try:
            src = sys.stdin.read()
        except KeyboardInterrupt:
            return
        toks = Lexer(src).tokenize()
        for t in toks:
            print(t)
        return

    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    lex = Lexer(src, filename=os.path.basename(path))
    print(f"==== Tokens of {path} ====")
    for t in lex.tokenize():
        print(t)


if __name__ == "__main__":
    main()
