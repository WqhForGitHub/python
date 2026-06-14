# -*- coding: utf-8 -*-
"""
简单解释器（表达式解析）
- 纯 Python 实现，无依赖
- 支持：
  * 算术：+ - * / % ** （右结合幂运算）
  * 比较：== != < <= > >=
  * 逻辑：and / or / not
  * 一元：- +
  * 括号 ( )
  * 数字（int / float）、字符串（'...'/"..."）、布尔、null
  * 变量：x = 1; x + 2
  * 函数调用：abs(-3), max(1, 2), len("abc"), sqrt(2)
  * 多语句以 ; 或换行分隔，最后一个表达式作为输出
- REPL：交互式 expr> 提示符

实现：词法分析 + 递归下降语法分析 + 树遍历求值

用法：
    python interp.py            # REPL
    python interp.py "1+2*3"    # 直接求值
"""
import math
import sys


# ---------- Token ----------
class Token:
    __slots__ = ("type", "value", "pos")
    def __init__(self, type_, value, pos):
        self.type, self.value, self.pos = type_, value, pos
    def __repr__(self): return f"<{self.type}:{self.value}>"


KEYWORDS = {"and", "or", "not", "true", "false", "null"}


# ---------- 词法分析 ----------
def tokenize(src):
    i, n = 0, len(src)
    tokens = []
    while i < n:
        c = src[i]
        if c in " \t\r":
            i += 1; continue
        if c == "\n" or c == ";":
            tokens.append(Token("SEP", c, i)); i += 1; continue
        if c == "#":
            while i < n and src[i] != "\n": i += 1
            continue

        # 数字
        if c.isdigit() or (c == "." and i + 1 < n and src[i + 1].isdigit()):
            j = i; has_dot = False; has_e = False
            while j < n:
                cj = src[j]
                if cj.isdigit():
                    j += 1
                elif cj == "." and not has_dot and not has_e:
                    has_dot = True; j += 1
                elif cj in "eE" and not has_e:
                    has_e = True; j += 1
                    if j < n and src[j] in "+-": j += 1
                else:
                    break
            text = src[i:j]
            value = float(text) if has_dot or has_e else int(text)
            tokens.append(Token("NUM", value, i)); i = j; continue

        # 字符串
        if c in "'\"":
            quote = c; j = i + 1; out = []
            while j < n and src[j] != quote:
                if src[j] == "\\" and j + 1 < n:
                    esc = src[j + 1]
                    out.append({"n": "\n", "t": "\t", "r": "\r",
                                "\\": "\\", "'": "'", '"': '"'}.get(esc, esc))
                    j += 2
                else:
                    out.append(src[j]); j += 1
            if j >= n:
                raise SyntaxError(f"未闭合字符串 @ {i}")
            tokens.append(Token("STR", "".join(out), i)); i = j + 1; continue

        # 标识符 / 关键字
        if c.isalpha() or c == "_":
            j = i + 1
            while j < n and (src[j].isalnum() or src[j] == "_"): j += 1
            text = src[i:j]
            if text in KEYWORDS:
                tokens.append(Token("KW", text, i))
            else:
                tokens.append(Token("ID", text, i))
            i = j; continue

        # 运算符
        two = src[i:i + 2]
        if two in ("==", "!=", "<=", ">=", "**"):
            tokens.append(Token("OP", two, i)); i += 2; continue
        if c in "+-*/%<>()=,":
            tokens.append(Token("OP", c, i)); i += 1; continue
        raise SyntaxError(f"非法字符 {c!r} @ {i}")

    tokens.append(Token("EOF", None, n))
    return tokens


# ---------- 语法树 ----------
class Node: pass
class Num(Node):
    def __init__(self, v): self.v = v
class Str(Node):
    def __init__(self, v): self.v = v
class Bool(Node):
    def __init__(self, v): self.v = v
class Null(Node): pass
class Var(Node):
    def __init__(self, name): self.name = name
class Assign(Node):
    def __init__(self, name, expr): self.name, self.expr = name, expr
class BinOp(Node):
    def __init__(self, op, l, r): self.op, self.l, self.r = op, l, r
class UnaryOp(Node):
    def __init__(self, op, e): self.op, self.e = op, e
class Call(Node):
    def __init__(self, name, args): self.name, self.args = name, args


# ---------- 解析器（递归下降） ----------
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens; self.pos = 0

    def peek(self, k=0): return self.tokens[self.pos + k]
    def eat(self, type_=None, value=None):
        t = self.tokens[self.pos]
        if type_ and t.type != type_: raise SyntaxError(f"期待 {type_}, 实得 {t}")
        if value and t.value != value: raise SyntaxError(f"期待 {value!r}, 实得 {t.value!r}")
        self.pos += 1; return t

    # program := stmt (SEP stmt)*
    def parse_program(self):
        stmts = []
        while self.peek().type == "SEP":
            self.pos += 1
        while self.peek().type != "EOF":
            stmts.append(self.parse_stmt())
            while self.peek().type == "SEP":
                self.pos += 1
        return stmts

    def parse_stmt(self):
        # 赋值：ID = expr
        if self.peek().type == "ID" and self.peek(1).type == "OP" and self.peek(1).value == "=":
            name = self.eat("ID").value
            self.eat("OP", "=")
            expr = self.parse_expr()
            return Assign(name, expr)
        return self.parse_expr()

    # 优先级（低 -> 高）：or, and, not, ==/!=, <,<=,>,>=, +-, */%, **, unary, primary
    def parse_expr(self): return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.peek().type == "KW" and self.peek().value == "or":
            self.eat(); right = self.parse_and()
            left = BinOp("or", left, right)
        return left

    def parse_and(self):
        left = self.parse_not()
        while self.peek().type == "KW" and self.peek().value == "and":
            self.eat(); right = self.parse_not()
            left = BinOp("and", left, right)
        return left

    def parse_not(self):
        if self.peek().type == "KW" and self.peek().value == "not":
            self.eat(); return UnaryOp("not", self.parse_not())
        return self.parse_eq()

    def parse_eq(self):
        left = self.parse_cmp()
        while self.peek().type == "OP" and self.peek().value in ("==", "!="):
            op = self.eat().value
            left = BinOp(op, left, self.parse_cmp())
        return left

    def parse_cmp(self):
        left = self.parse_add()
        while self.peek().type == "OP" and self.peek().value in ("<", "<=", ">", ">="):
            op = self.eat().value
            left = BinOp(op, left, self.parse_add())
        return left

    def parse_add(self):
        left = self.parse_mul()
        while self.peek().type == "OP" and self.peek().value in ("+", "-"):
            op = self.eat().value
            left = BinOp(op, left, self.parse_mul())
        return left

    def parse_mul(self):
        left = self.parse_unary()
        while self.peek().type == "OP" and self.peek().value in ("*", "/", "%"):
            op = self.eat().value
            left = BinOp(op, left, self.parse_unary())
        return left

    def parse_unary(self):
        if self.peek().type == "OP" and self.peek().value in ("+", "-"):
            op = self.eat().value
            return UnaryOp(op, self.parse_unary())
        return self.parse_pow()

    def parse_pow(self):
        # 右结合
        left = self.parse_primary()
        if self.peek().type == "OP" and self.peek().value == "**":
            self.eat()
            return BinOp("**", left, self.parse_unary())
        return left

    def parse_primary(self):
        t = self.peek()
        if t.type == "NUM":
            self.eat(); return Num(t.value)
        if t.type == "STR":
            self.eat(); return Str(t.value)
        if t.type == "KW" and t.value in ("true", "false"):
            self.eat(); return Bool(t.value == "true")
        if t.type == "KW" and t.value == "null":
            self.eat(); return Null()
        if t.type == "OP" and t.value == "(":
            self.eat(); e = self.parse_expr(); self.eat("OP", ")"); return e
        if t.type == "ID":
            name = self.eat().value
            if self.peek().type == "OP" and self.peek().value == "(":
                self.eat(); args = []
                if not (self.peek().type == "OP" and self.peek().value == ")"):
                    args.append(self.parse_expr())
                    while self.peek().type == "OP" and self.peek().value == ",":
                        self.eat(); args.append(self.parse_expr())
                self.eat("OP", ")")
                return Call(name, args)
            return Var(name)
        raise SyntaxError(f"非预期 token: {t}")


# ---------- 求值器 ----------
BUILTINS = {
    "abs": abs, "min": min, "max": max, "len": len,
    "int": int, "float": float, "str": str, "bool": bool,
    "round": round, "pow": pow,
    "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "log": math.log, "exp": math.exp, "floor": math.floor, "ceil": math.ceil,
    "print": print,
}


class Interpreter:
    def __init__(self):
        self.env = {}

    def eval(self, src):
        tokens = tokenize(src)
        ast = Parser(tokens).parse_program()
        last = None
        for stmt in ast:
            last = self.visit(stmt)
        return last

    def visit(self, node):
        m = getattr(self, f"v_{type(node).__name__}")
        return m(node)

    def v_Num(self, n):  return n.v
    def v_Str(self, n):  return n.v
    def v_Bool(self, n): return n.v
    def v_Null(self, n): return None

    def v_Var(self, n):
        if n.name in self.env: return self.env[n.name]
        if n.name in BUILTINS: return BUILTINS[n.name]
        raise NameError(f"未定义 {n.name}")

    def v_Assign(self, n):
        val = self.visit(n.expr)
        self.env[n.name] = val
        return val

    def v_UnaryOp(self, n):
        v = self.visit(n.e)
        if n.op == "+": return +v
        if n.op == "-": return -v
        if n.op == "not": return not v
        raise SyntaxError(f"未知一元 {n.op}")

    def v_BinOp(self, n):
        if n.op == "and":
            l = self.visit(n.l); return self.visit(n.r) if l else l
        if n.op == "or":
            l = self.visit(n.l); return l if l else self.visit(n.r)
        a, b = self.visit(n.l), self.visit(n.r)
        op = n.op
        if op == "+": return a + b
        if op == "-": return a - b
        if op == "*": return a * b
        if op == "/": return a / b
        if op == "%": return a % b
        if op == "**": return a ** b
        if op == "==": return a == b
        if op == "!=": return a != b
        if op == "<":  return a < b
        if op == "<=": return a <= b
        if op == ">":  return a > b
        if op == ">=": return a >= b
        raise SyntaxError(f"未知运算 {op}")

    def v_Call(self, n):
        if n.name in self.env and callable(self.env[n.name]):
            fn = self.env[n.name]
        elif n.name in BUILTINS:
            fn = BUILTINS[n.name]
        else:
            raise NameError(f"未定义函数 {n.name}")
        args = [self.visit(a) for a in n.args]
        return fn(*args)


# ---------- REPL ----------
def repl():
    interp = Interpreter()
    print("Mini Interpreter — 输入表达式，:q 退出")
    while True:
        try:
            line = input("expr> ")
        except (EOFError, KeyboardInterrupt):
            print(); break
        if not line.strip(): continue
        if line.strip() in (":q", "exit", "quit"):
            break
        try:
            r = interp.eval(line)
            if r is not None:
                print(repr(r))
        except Exception as e:
            print(f"错误: {e}")


def main():
    if len(sys.argv) > 1:
        src = " ".join(sys.argv[1:])
        print(Interpreter().eval(src))
    else:
        repl()


if __name__ == "__main__":
    main()
