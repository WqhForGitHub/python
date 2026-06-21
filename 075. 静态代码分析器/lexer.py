# -*- coding: utf-8 -*-
"""
词法分析器（独立实现 / 状态机版）
- 不依赖 re 模块，使用手写字符级状态机扫描
- 识别：
  * 整数 / 浮点 / 十六进制 / 二进制
  * 字符串（双引号 / 单引号，含转义）
  * 标识符 / 关键字（C 风格）
  * 运算符与标点（含 ==, !=, <=, >=, &&, ||, +=, -=, ->, ::, .. 等）
  * 行注释 //  与块注释 /* ... */
- 携带源文件 / 行 / 列信息
- 错误报告附带上下文（行内容 + 指针）
- 命令行：python lexer.py <file>

注：此实现独立于其它目录的 lexer 实现（手写扫描，无正则）。

用法：
    python lexer.py             # 内置 demo 字符串
    python lexer.py demo.src    # 指定源文件
"""
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ---------- 数据结构 ----------
@dataclass
class Token:
    kind: str
    value: object
    line: int
    col: int
    length: int = 0
    text: str = ""

    def __str__(self):
        v = repr(self.value) if self.value is not None else ""
        return f"{self.line:>4}:{self.col:<4}  {self.kind:<10}  {v}"


class LexError(Exception):
    pass


KEYWORDS = {
    "if", "else", "while", "do", "for", "switch", "case", "default",
    "break", "continue", "return", "true", "false", "null", "void",
    "int", "float", "bool", "string", "let", "const", "fn", "class",
    "new", "this", "import", "export", "and", "or", "not",
}


# ---------- 字符工具 ----------
def is_ident_start(c): return c.isalpha() or c == "_"
def is_ident_cont(c):  return c.isalnum() or c == "_"
def is_digit(c):       return "0" <= c <= "9"
def is_hex(c):         return is_digit(c) or "a" <= c.lower() <= "f"
def is_bin(c):         return c in "01"


# ---------- 扫描器 ----------
class Lexer:
    def __init__(self, src, filename="<source>"):
        self.src = src
        self.filename = filename
        self.i = 0
        self.line = 1
        self.col = 1
        self.tokens = []

    # 基本辅助
    def _peek(self, k=0):
        j = self.i + k
        return self.src[j] if j < len(self.src) else ""

    def _eof(self):
        return self.i >= len(self.src)

    def _advance(self):
        c = self.src[self.i]
        self.i += 1
        if c == "\n":
            self.line += 1; self.col = 1
        else:
            self.col += 1
        return c

    def _match(self, expected):
        if self._peek() == expected:
            self._advance(); return True
        return False

    def _emit(self, kind, value, start_line, start_col, start_idx):
        text = self.src[start_idx:self.i]
        self.tokens.append(Token(kind, value, start_line, start_col, len(text), text))

    def _error(self, msg, line=None, col=None):
        line = line if line is not None else self.line
        col = col if col is not None else self.col
        # 取出所在行内容
        lines = self.src.split("\n")
        ln_text = lines[line - 1] if 0 < line <= len(lines) else ""
        ptr = " " * (col - 1) + "^"
        full = f"{self.filename}:{line}:{col}: {msg}\n  {ln_text}\n  {ptr}"
        raise LexError(full)

    # ---- 主循环 ----
    def tokenize(self):
        while not self._eof():
            self._skip_trivia()
            if self._eof(): break
            start_line, start_col, start_idx = self.line, self.col, self.i
            c = self._peek()

            if is_ident_start(c):
                self._scan_ident(start_line, start_col, start_idx)
            elif is_digit(c) or (c == "." and is_digit(self._peek(1))):
                self._scan_number(start_line, start_col, start_idx)
            elif c == '"' or c == "'":
                self._scan_string(start_line, start_col, start_idx)
            else:
                self._scan_operator(start_line, start_col, start_idx)

        self.tokens.append(Token("EOF", None, self.line, self.col))
        return self.tokens

    # ---- 跳过空白 / 注释 ----
    def _skip_trivia(self):
        while not self._eof():
            c = self._peek()
            if c in " \t\r\n":
                self._advance()
            elif c == "/" and self._peek(1) == "/":
                while not self._eof() and self._peek() != "\n":
                    self._advance()
            elif c == "/" and self._peek(1) == "*":
                self._advance(); self._advance()
                start_line, start_col = self.line, self.col
                while not self._eof():
                    if self._peek() == "*" and self._peek(1) == "/":
                        self._advance(); self._advance(); break
                    self._advance()
                else:
                    self._error("未闭合块注释", start_line, start_col)
            else:
                break

    # ---- 标识符 / 关键字 ----
    def _scan_ident(self, sl, sc, si):
        while not self._eof() and is_ident_cont(self._peek()):
            self._advance()
        text = self.src[si:self.i]
        if text in KEYWORDS:
            kind = "KEYWORD"
            value = text
        elif text == "true":
            kind, value = "BOOL", True
        elif text == "false":
            kind, value = "BOOL", False
        elif text == "null":
            kind, value = "NULL", None
        else:
            kind, value = "IDENT", text
        self._emit(kind, value, sl, sc, si)

    # ---- 数字 ----
    def _scan_number(self, sl, sc, si):
        # 0x / 0b 前缀
        if self._peek() == "0" and self._peek(1) in "xXbB":
            self._advance()
            base_char = self._advance()
            if base_char in "xX":
                if not is_hex(self._peek()):
                    self._error("无效的十六进制数字", sl, sc)
                while is_hex(self._peek()):
                    self._advance()
                value = int(self.src[si:self.i], 16)
            else:
                if not is_bin(self._peek()):
                    self._error("无效的二进制数字", sl, sc)
                while is_bin(self._peek()):
                    self._advance()
                value = int(self.src[si + 2:self.i], 2)
            self._emit("INT", value, sl, sc, si)
            return

        is_float = False
        # 整数部分
        while is_digit(self._peek()):
            self._advance()
        # 小数部分
        if self._peek() == "." and is_digit(self._peek(1)):
            is_float = True
            self._advance()
            while is_digit(self._peek()):
                self._advance()
        # 指数部分
        if self._peek() in "eE":
            is_float = True
            self._advance()
            if self._peek() in "+-":
                self._advance()
            if not is_digit(self._peek()):
                self._error("指数缺少数字", sl, sc)
            while is_digit(self._peek()):
                self._advance()
        text = self.src[si:self.i]
        if is_float:
            self._emit("FLOAT", float(text), sl, sc, si)
        else:
            self._emit("INT", int(text), sl, sc, si)

    # ---- 字符串 ----
    def _scan_string(self, sl, sc, si):
        quote = self._advance()
        out = []
        while not self._eof() and self._peek() != quote:
            ch = self._peek()
            if ch == "\n":
                self._error("字符串中含未转义换行", sl, sc)
            if ch == "\\":
                self._advance()
                esc = self._advance() if not self._eof() else ""
                out.append({
                    "n": "\n", "t": "\t", "r": "\r", "0": "\0",
                    "\\": "\\", "'": "'", '"': '"',
                }.get(esc, esc))
            else:
                out.append(self._advance())
        if self._eof():
            self._error("未闭合字符串", sl, sc)
        self._advance()  # 消耗末尾引号
        self._emit("STRING", "".join(out), sl, sc, si)

    # ---- 运算符 / 标点 ----
    _SINGLE = set("+-*/%=<>!&|^~?:.,;(){}[]@")

    def _scan_operator(self, sl, sc, si):
        c = self._advance()
        # 三字符
        if c == "." and self._peek() == "." and self._peek(1) == ".":
            self._advance(); self._advance()
            self._emit("OP", "...", sl, sc, si); return
        # 双字符
        two = c + self._peek()
        if two in ("==", "!=", "<=", ">=", "&&", "||", "->", "=>",
                   "::", "..", "++", "--", "+=", "-=", "*=", "/=", "%=",
                   "<<", ">>", "**"):
            self._advance()
            self._emit("OP", two, sl, sc, si); return
        if c in self._SINGLE:
            self._emit("OP", c, sl, sc, si); return
        self._error(f"非法字符 {c!r}", sl, sc)


# ---------- demo ----------
DEMO_SRC = '''// 一段示例源代码
fn factorial(n) {
    if n <= 1 { return 1 }
    return n * factorial(n - 1)
}

let pi = 3.1415926
let hex = 0xFF
let bin = 0b1010
let s = "Hello\\n\\"World\\""
let r = pi * 2.0e1

/* 多行
   注释 */

if hex >= 100 && bin > 0 {
    print("OK", factorial(5))
}
'''


def main():
    if len(sys.argv) > 1:
        path = sys.argv[1]
        src = Path(path).read_text(encoding="utf-8")
        filename = path
    else:
        src = DEMO_SRC
        filename = "<demo>"

    try:
        tokens = Lexer(src, filename=filename).tokenize()
    except LexError as e:
        print("词法错误:")
        print(e); sys.exit(1)

    print(f"==== Tokens of {filename} ====")
    print(f"{'line:col':<10} {'kind':<10}  value")
    print("-" * 50)
    for t in tokens:
        print(t)
    print(f"\n共 {len(tokens)} 个 token")


if __name__ == "__main__":
    main()
