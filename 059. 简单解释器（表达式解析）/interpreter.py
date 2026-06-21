# -*- coding: utf-8 -*-
"""
简单解释器（表达式解析）
- 完整的递归下降解析器
- 支持： + - * / % ** 一元正负 括号
- 支持变量赋值 (x = 1+2)、变量引用
- 支持函数调用：sin/cos/sqrt/abs/min/max
- REPL 交互模式

文法：
    statement := IDENT '=' expr | expr
    expr      := term  (('+'|'-') term)*
    term      := factor (('*'|'/'|'%') factor)*
    factor    := unary ('**' factor)?     # 右结合
    unary     := ('+'|'-') unary | atom
    atom      := NUMBER | IDENT ['(' args ')'] | '(' expr ')'
"""
import math
import sys


class Token:
    def __init__(self, kind, value):
        self.kind = kind
        self.value = value
    def __repr__(self):
        return f"Token({self.kind},{self.value!r})"


def tokenize(text):
    tokens = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c.isspace():
            i += 1
            continue
        if c.isdigit() or (c == "." and i + 1 < n and text[i+1].isdigit()):
            j = i
            dot = False
            while j < n and (text[j].isdigit() or text[j] == "."):
                if text[j] == ".":
                    if dot:
                        break
                    dot = True
                j += 1
            tokens.append(Token("NUM", float(text[i:j]) if dot else int(text[i:j])))
            i = j
            continue
        if c.isalpha() or c == "_":
            j = i
            while j < n and (text[j].isalnum() or text[j] == "_"):
                j += 1
            tokens.append(Token("IDENT", text[i:j]))
            i = j
            continue
        if c == "*" and i + 1 < n and text[i+1] == "*":
            tokens.append(Token("OP", "**"))
            i += 2
            continue
        if c in "+-*/%(),=":
            tokens.append(Token("OP", c))
            i += 1
            continue
        raise SyntaxError(f"非法字符: {c!r} at {i}")
    tokens.append(Token("EOF", None))
    return tokens


class Parser:
    def __init__(self, tokens, env):
        self.tokens = tokens
        self.pos = 0
        self.env = env

    def peek(self, offset=0):
        return self.tokens[self.pos + offset]

    def eat(self, kind=None, value=None):
        tok = self.tokens[self.pos]
        if kind and tok.kind != kind:
            raise SyntaxError(f"期望 {kind}, 实际 {tok}")
        if value is not None and tok.value != value:
            raise SyntaxError(f"期望 {value!r}, 实际 {tok.value!r}")
        self.pos += 1
        return tok

    def parse(self):
        # 赋值或表达式
        if self.peek().kind == "IDENT" and self.peek(1).kind == "OP" and self.peek(1).value == "=":
            name = self.eat("IDENT").value
            self.eat("OP", "=")
            value = self.expr()
            self.env[name] = value
            return value
        return self.expr()

    def expr(self):
        v = self.term()
        while self.peek().kind == "OP" and self.peek().value in ("+", "-"):
            op = self.eat("OP").value
            r = self.term()
            v = v + r if op == "+" else v - r
        return v

    def term(self):
        v = self.factor()
        while self.peek().kind == "OP" and self.peek().value in ("*", "/", "%"):
            op = self.eat("OP").value
            r = self.factor()
            if op == "*":
                v = v * r
            elif op == "/":
                v = v / r
            else:
                v = v % r
        return v

    def factor(self):
        v = self.unary()
        if self.peek().kind == "OP" and self.peek().value == "**":
            self.eat("OP", "**")
            r = self.factor()  # 右结合
            v = v ** r
        return v

    def unary(self):
        if self.peek().kind == "OP" and self.peek().value in ("+", "-"):
            op = self.eat("OP").value
            v = self.unary()
            return -v if op == "-" else +v
        return self.atom()

    def atom(self):
        tok = self.peek()
        if tok.kind == "NUM":
            self.eat("NUM")
            return tok.value
        if tok.kind == "IDENT":
            self.eat("IDENT")
            name = tok.value
            # 函数调用
            if self.peek().kind == "OP" and self.peek().value == "(":
                self.eat("OP", "(")
                args = []
                if not (self.peek().kind == "OP" and self.peek().value == ")"):
                    args.append(self.expr())
                    while self.peek().kind == "OP" and self.peek().value == ",":
                        self.eat("OP", ",")
                        args.append(self.expr())
                self.eat("OP", ")")
                fn = self.env.get(name)
                if not callable(fn):
                    raise NameError(f"未定义函数: {name}")
                return fn(*args)
            # 变量
            if name in self.env:
                v = self.env[name]
                if callable(v):
                    raise SyntaxError(f"{name} 是函数，需带 ()")
                return v
            raise NameError(f"未定义变量: {name}")
        if tok.kind == "OP" and tok.value == "(":
            self.eat("OP", "(")
            v = self.expr()
            self.eat("OP", ")")
            return v
        raise SyntaxError(f"意外的 token: {tok}")


def make_env():
    return {
        "pi": math.pi, "e": math.e,
        "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "sqrt": math.sqrt, "abs": abs, "min": min, "max": max,
        "log": math.log, "exp": math.exp, "pow": pow,
    }


def evaluate(text, env=None):
    env = env if env is not None else make_env()
    tokens = tokenize(text)
    return Parser(tokens, env).parse()


def repl():
    env = make_env()
    print("简单解释器 REPL（输入 quit 退出）")
    while True:
        try:
            line = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line in ("quit", "exit"):
            break
        try:
            result = evaluate(line, env)
            env["_"] = result
            print(result)
        except Exception as e:
            print(f"[错误] {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 命令行参数表达式
        print(evaluate(" ".join(sys.argv[1:])))
    else:
        repl()
