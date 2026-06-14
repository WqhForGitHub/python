# -*- coding: utf-8 -*-
"""
语法解析器 (Parser)
- 针对算术 + 比较 + 布尔表达式的递归下降解析器
- 输出 AST，可打印为 S 表达式或树形

支持文法：
    expr   := or
    or     := and ('or' and)*
    and    := not ('and' not)*
    not    := 'not' not | comp
    comp   := add (('<'|'>'|'<='|'>='|'=='|'!=') add)?
    add    := mul (('+'|'-') mul)*
    mul    := pow (('*'|'/'|'%') pow)*
    pow    := unary ('**' pow)?
    unary  := ('+'|'-') unary | atom
    atom   := NUMBER | IDENT ['(' args ')'] | '(' expr ')'

用法：
    python parser.py "1 + 2 * 3"
    python parser.py "a*(b+c) > 0 and not flag"
"""
import re
import sys


# ---- Lexer ----
TOKEN_RE = re.compile(
    r"\s*(?:"
    r"(?P<NUMBER>\d+(?:\.\d+)?)"
    r"|(?P<IDENT>[A-Za-z_][A-Za-z_0-9]*)"
    r"|(?P<OP>\*\*|<=|>=|==|!=|[+\-*/%<>(),])"
    r")"
)
KEYWORDS = {"and", "or", "not"}


def tokenize(src):
    pos = 0
    tokens = []
    while pos < len(src):
        if src[pos].isspace():
            pos += 1; continue
        m = TOKEN_RE.match(src, pos)
        if not m or m.start() != pos:
            raise SyntaxError(f"非法字符 {src[pos]!r} at {pos}")
        kind = m.lastgroup
        value = m.group(kind)
        if kind == "NUMBER":
            value = float(value) if "." in value else int(value)
        elif kind == "IDENT" and value in KEYWORDS:
            kind = "KW"
        tokens.append((kind, value))
        pos = m.end()
    tokens.append(("EOF", None))
    return tokens


# ---- AST ----
class Node:
    pass


class Num(Node):
    def __init__(self, v): self.v = v
    def s(self): return str(self.v)


class Var(Node):
    def __init__(self, n): self.n = n
    def s(self): return self.n


class BinOp(Node):
    def __init__(self, op, l, r): self.op, self.l, self.r = op, l, r
    def s(self): return f"({self.op} {self.l.s()} {self.r.s()})"


class UnaryOp(Node):
    def __init__(self, op, e): self.op, self.e = op, e
    def s(self): return f"({self.op}u {self.e.s()})"


class Call(Node):
    def __init__(self, name, args): self.name, self.args = name, args
    def s(self): return f"(call {self.name} {' '.join(a.s() for a in self.args)})"


# ---- Parser ----
class Parser:
    def __init__(self, tokens):
        self.tokens, self.pos = tokens, 0

    def peek(self): return self.tokens[self.pos]

    def eat(self, kind=None, value=None):
        tok = self.peek()
        if kind and tok[0] != kind:
            raise SyntaxError(f"期望 {kind} 实际 {tok}")
        if value is not None and tok[1] != value:
            raise SyntaxError(f"期望 {value!r} 实际 {tok[1]!r}")
        self.pos += 1
        return tok

    def parse(self):
        e = self.expr()
        if self.peek()[0] != "EOF":
            raise SyntaxError(f"残留 token: {self.peek()}")
        return e

    def expr(self): return self.or_()

    def or_(self):
        v = self.and_()
        while self.peek()[0] == "KW" and self.peek()[1] == "or":
            self.eat()
            v = BinOp("or", v, self.and_())
        return v

    def and_(self):
        v = self.not_()
        while self.peek()[0] == "KW" and self.peek()[1] == "and":
            self.eat()
            v = BinOp("and", v, self.not_())
        return v

    def not_(self):
        if self.peek()[0] == "KW" and self.peek()[1] == "not":
            self.eat()
            return UnaryOp("not", self.not_())
        return self.comp()

    def comp(self):
        v = self.add()
        if self.peek()[0] == "OP" and self.peek()[1] in ("<", ">", "<=", ">=", "==", "!="):
            op = self.eat()[1]
            v = BinOp(op, v, self.add())
        return v

    def add(self):
        v = self.mul()
        while self.peek()[0] == "OP" and self.peek()[1] in ("+", "-"):
            op = self.eat()[1]
            v = BinOp(op, v, self.mul())
        return v

    def mul(self):
        v = self.pow_()
        while self.peek()[0] == "OP" and self.peek()[1] in ("*", "/", "%"):
            op = self.eat()[1]
            v = BinOp(op, v, self.pow_())
        return v

    def pow_(self):
        v = self.unary()
        if self.peek()[0] == "OP" and self.peek()[1] == "**":
            self.eat()
            v = BinOp("**", v, self.pow_())  # 右结合
        return v

    def unary(self):
        if self.peek()[0] == "OP" and self.peek()[1] in ("+", "-"):
            op = self.eat()[1]
            return UnaryOp(op, self.unary())
        return self.atom()

    def atom(self):
        tok = self.peek()
        if tok[0] == "NUMBER":
            self.eat(); return Num(tok[1])
        if tok[0] == "IDENT":
            self.eat()
            if self.peek()[0] == "OP" and self.peek()[1] == "(":
                self.eat("OP", "(")
                args = []
                if not (self.peek()[0] == "OP" and self.peek()[1] == ")"):
                    args.append(self.expr())
                    while self.peek()[0] == "OP" and self.peek()[1] == ",":
                        self.eat(); args.append(self.expr())
                self.eat("OP", ")")
                return Call(tok[1], args)
            return Var(tok[1])
        if tok[0] == "OP" and tok[1] == "(":
            self.eat()
            v = self.expr()
            self.eat("OP", ")")
            return v
        raise SyntaxError(f"意外 token: {tok}")


# ---- Tree printer ----
def tree(node, prefix="", is_last=True):
    if isinstance(node, BinOp):
        label = f"BinOp[{node.op}]"
        children = [node.l, node.r]
    elif isinstance(node, UnaryOp):
        label = f"Unary[{node.op}]"
        children = [node.e]
    elif isinstance(node, Call):
        label = f"Call[{node.name}]"
        children = node.args
    elif isinstance(node, Num):
        label = f"Num({node.v})"; children = []
    elif isinstance(node, Var):
        label = f"Var({node.n})"; children = []
    else:
        label = repr(node); children = []
    branch = "└── " if is_last else "├── "
    print(prefix + branch + label)
    new_prefix = prefix + ("    " if is_last else "│   ")
    for i, c in enumerate(children):
        tree(c, new_prefix, i == len(children) - 1)


def main():
    if len(sys.argv) < 2:
        src = "1 + 2 * 3 - x ** 2"
    else:
        src = " ".join(sys.argv[1:])
    print(f"输入: {src}")
    tokens = tokenize(src)
    print("Tokens:", tokens)
    ast = Parser(tokens).parse()
    print("S-expr:", ast.s())
    print("Tree:")
    tree(ast)


if __name__ == "__main__":
    main()
