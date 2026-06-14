# -*- coding: utf-8 -*-
"""
自定义编程语言（极简）—— "MiniLang"
- 语法风格类 Python，但实现极简
- 支持：
    let x = expr            变量声明/赋值
    print(expr [, expr]*)   打印
    if cond { ... } else { ... }
    while cond { ... }
    fn name(a, b) { ... return expr }
    赋值/算术/比较/逻辑/字符串/数字/布尔
- 完整流程：lexer -> parser -> tree-walking interpreter

示例程序见 examples/fib.ml
用法：
    python minilang.py examples/fib.ml
"""
import os
import sys
import re


# ---------------- Lexer ----------------
TOKEN_SPEC = [
    ("COMMENT", r"//[^\n]*"),
    ("NUMBER",  r"\d+(\.\d*)?"),
    ("STRING",  r'"([^"\\]|\\.)*"'),
    ("ID",      r"[A-Za-z_][A-Za-z_0-9]*"),
    ("OP",      r"==|!=|<=|>=|&&|\|\||[+\-*/%<>=!{}(),;]"),
    ("NEWLINE", r"\n"),
    ("SKIP",    r"[ \t\r]+"),
]
TOKEN_RE = re.compile("|".join(f"(?P<{n}>{p})" for n, p in TOKEN_SPEC))
KEYWORDS = {"let", "if", "else", "while", "fn", "return", "true", "false", "null", "print"}


def tokenize(src):
    tokens = []
    line = 1
    for m in TOKEN_RE.finditer(src):
        kind = m.lastgroup
        val = m.group()
        if kind == "NEWLINE":
            line += 1
            continue
        if kind in ("SKIP", "COMMENT"):
            continue
        if kind == "NUMBER":
            val = float(val) if "." in val else int(val)
        elif kind == "STRING":
            val = bytes(val[1:-1], "utf-8").decode("unicode_escape")
        elif kind == "ID":
            if val in KEYWORDS:
                kind = val.upper()
        tokens.append((kind, val, line))
    tokens.append(("EOF", None, line))
    return tokens


# ---------------- AST ----------------
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
class BinOp(Node):
    def __init__(self, op, l, r): self.op, self.l, self.r = op, l, r
class UnaryOp(Node):
    def __init__(self, op, e): self.op, self.e = op, e
class Assign(Node):
    def __init__(self, name, value, decl=False):
        self.name, self.value, self.decl = name, value, decl
class Print(Node):
    def __init__(self, args): self.args = args
class If(Node):
    def __init__(self, cond, t, f): self.cond, self.t, self.f = cond, t, f
class While(Node):
    def __init__(self, cond, body): self.cond, self.body = cond, body
class Block(Node):
    def __init__(self, stmts): self.stmts = stmts
class FnDef(Node):
    def __init__(self, name, params, body): self.name, self.params, self.body = name, params, body
class Call(Node):
    def __init__(self, callee, args): self.callee, self.args = callee, args
class Return(Node):
    def __init__(self, e): self.e = e


# ---------------- Parser ----------------
class Parser:
    def __init__(self, tokens):
        self.tokens, self.pos = tokens, 0

    def peek(self, k=0): return self.tokens[self.pos + k]
    def eat(self, kind=None, val=None):
        tok = self.tokens[self.pos]
        if kind and tok[0] != kind:
            raise SyntaxError(f"line {tok[2]}: 期望 {kind}, 实际 {tok}")
        if val is not None and tok[1] != val:
            raise SyntaxError(f"line {tok[2]}: 期望 {val!r}, 实际 {tok[1]!r}")
        self.pos += 1
        return tok

    def parse(self):
        stmts = []
        while self.peek()[0] != "EOF":
            stmts.append(self.statement())
        return Block(stmts)

    def statement(self):
        kind, val, _ = self.peek()
        if kind == "LET":
            return self.let_stmt()
        if kind == "IF":
            return self.if_stmt()
        if kind == "WHILE":
            return self.while_stmt()
        if kind == "FN":
            return self.fn_def()
        if kind == "RETURN":
            self.eat("RETURN")
            e = None
            if self.peek()[0] != "OP" or self.peek()[1] != ";":
                e = self.expr()
            self._consume_semi()
            return Return(e)
        if kind == "PRINT":
            return self.print_stmt()
        # 赋值或表达式
        if kind == "ID" and self.peek(1)[0] == "OP" and self.peek(1)[1] == "=":
            name = self.eat("ID")[1]
            self.eat("OP", "=")
            value = self.expr()
            self._consume_semi()
            return Assign(name, value, decl=False)
        e = self.expr()
        self._consume_semi()
        return e

    def _consume_semi(self):
        if self.peek()[0] == "OP" and self.peek()[1] == ";":
            self.eat("OP", ";")

    def let_stmt(self):
        self.eat("LET")
        name = self.eat("ID")[1]
        self.eat("OP", "=")
        value = self.expr()
        self._consume_semi()
        return Assign(name, value, decl=True)

    def print_stmt(self):
        self.eat("PRINT")
        self.eat("OP", "(")
        args = []
        if not (self.peek()[0] == "OP" and self.peek()[1] == ")"):
            args.append(self.expr())
            while self.peek()[0] == "OP" and self.peek()[1] == ",":
                self.eat("OP", ",")
                args.append(self.expr())
        self.eat("OP", ")")
        self._consume_semi()
        return Print(args)

    def if_stmt(self):
        self.eat("IF")
        cond = self.expr()
        t = self.block()
        f = None
        if self.peek()[0] == "ELSE":
            self.eat("ELSE")
            if self.peek()[0] == "IF":
                f = Block([self.if_stmt()])
            else:
                f = self.block()
        return If(cond, t, f)

    def while_stmt(self):
        self.eat("WHILE")
        cond = self.expr()
        body = self.block()
        return While(cond, body)

    def fn_def(self):
        self.eat("FN")
        name = self.eat("ID")[1]
        self.eat("OP", "(")
        params = []
        if not (self.peek()[0] == "OP" and self.peek()[1] == ")"):
            params.append(self.eat("ID")[1])
            while self.peek()[0] == "OP" and self.peek()[1] == ",":
                self.eat("OP", ",")
                params.append(self.eat("ID")[1])
        self.eat("OP", ")")
        body = self.block()
        return FnDef(name, params, body)

    def block(self):
        self.eat("OP", "{")
        stmts = []
        while not (self.peek()[0] == "OP" and self.peek()[1] == "}"):
            stmts.append(self.statement())
        self.eat("OP", "}")
        return Block(stmts)

    # --- 表达式优先级 ---
    def expr(self): return self.logic_or()

    def logic_or(self):
        v = self.logic_and()
        while self.peek()[0] == "OP" and self.peek()[1] == "||":
            self.eat()
            v = BinOp("||", v, self.logic_and())
        return v

    def logic_and(self):
        v = self.equality()
        while self.peek()[0] == "OP" and self.peek()[1] == "&&":
            self.eat()
            v = BinOp("&&", v, self.equality())
        return v

    def equality(self):
        v = self.comparison()
        while self.peek()[0] == "OP" and self.peek()[1] in ("==", "!="):
            op = self.eat()[1]
            v = BinOp(op, v, self.comparison())
        return v

    def comparison(self):
        v = self.add()
        while self.peek()[0] == "OP" and self.peek()[1] in ("<", ">", "<=", ">="):
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
        v = self.unary()
        while self.peek()[0] == "OP" and self.peek()[1] in ("*", "/", "%"):
            op = self.eat()[1]
            v = BinOp(op, v, self.unary())
        return v

    def unary(self):
        if self.peek()[0] == "OP" and self.peek()[1] in ("+", "-", "!"):
            op = self.eat()[1]
            return UnaryOp(op, self.unary())
        return self.call()

    def call(self):
        v = self.atom()
        while self.peek()[0] == "OP" and self.peek()[1] == "(":
            self.eat("OP", "(")
            args = []
            if not (self.peek()[0] == "OP" and self.peek()[1] == ")"):
                args.append(self.expr())
                while self.peek()[0] == "OP" and self.peek()[1] == ",":
                    self.eat("OP", ",")
                    args.append(self.expr())
            self.eat("OP", ")")
            v = Call(v, args)
        return v

    def atom(self):
        kind, val, _ = self.peek()
        if kind == "NUMBER":
            self.eat(); return Num(val)
        if kind == "STRING":
            self.eat(); return Str(val)
        if kind == "TRUE":
            self.eat(); return Bool(True)
        if kind == "FALSE":
            self.eat(); return Bool(False)
        if kind == "NULL":
            self.eat(); return Null()
        if kind == "ID":
            self.eat(); return Var(val)
        if kind == "OP" and val == "(":
            self.eat()
            v = self.expr()
            self.eat("OP", ")")
            return v
        raise SyntaxError(f"意外 token: {self.peek()}")


# ---------------- Interpreter ----------------
class Env:
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent
    def get(self, name):
        if name in self.vars:
            return self.vars[name]
        if self.parent:
            return self.parent.get(name)
        raise NameError(f"未定义: {name}")
    def set(self, name, value):
        # 已存在则更新到对应层
        env = self
        while env:
            if name in env.vars:
                env.vars[name] = value
                return
            env = env.parent
        raise NameError(f"未定义: {name}")
    def declare(self, name, value):
        self.vars[name] = value


class Function:
    def __init__(self, defn, closure):
        self.defn = defn
        self.closure = closure


class ReturnSignal(Exception):
    def __init__(self, value): self.value = value


class Interpreter:
    def __init__(self):
        self.global_env = Env()

    def run(self, program):
        return self.exec_block(program, self.global_env)

    def exec_block(self, block, env):
        result = None
        for s in block.stmts:
            result = self.exec(s, env)
        return result

    def exec(self, node, env):
        m = "exec_" + type(node).__name__
        return getattr(self, m)(node, env)

    def exec_Block(self, n, env):
        scope = Env(env)
        return self.exec_block(n, scope)

    def exec_Num(self, n, env): return n.v
    def exec_Str(self, n, env): return n.v
    def exec_Bool(self, n, env): return n.v
    def exec_Null(self, n, env): return None
    def exec_Var(self, n, env): return env.get(n.name)

    def exec_Assign(self, n, env):
        value = self.exec(n.value, env)
        if n.decl:
            env.declare(n.name, value)
        else:
            try:
                env.set(n.name, value)
            except NameError:
                env.declare(n.name, value)
        return value

    def exec_Print(self, n, env):
        vals = [self.exec(a, env) for a in n.args]
        print(*[self._to_str(v) for v in vals])

    @staticmethod
    def _to_str(v):
        if v is True: return "true"
        if v is False: return "false"
        if v is None: return "null"
        return str(v)

    def exec_If(self, n, env):
        if self._truthy(self.exec(n.cond, env)):
            return self.exec(n.t, env)
        if n.f:
            return self.exec(n.f, env)

    def exec_While(self, n, env):
        while self._truthy(self.exec(n.cond, env)):
            self.exec(n.body, env)

    def exec_FnDef(self, n, env):
        env.declare(n.name, Function(n, env))

    def exec_Call(self, n, env):
        callee = self.exec(n.callee, env)
        args = [self.exec(a, env) for a in n.args]
        if isinstance(callee, Function):
            scope = Env(callee.closure)
            for p, a in zip(callee.defn.params, args):
                scope.declare(p, a)
            try:
                self.exec_block(callee.defn.body, scope)
            except ReturnSignal as r:
                return r.value
            return None
        if callable(callee):
            return callee(*args)
        raise TypeError("不可调用")

    def exec_Return(self, n, env):
        v = self.exec(n.e, env) if n.e else None
        raise ReturnSignal(v)

    def exec_BinOp(self, n, env):
        if n.op == "&&":
            a = self.exec(n.l, env)
            return self.exec(n.r, env) if self._truthy(a) else a
        if n.op == "||":
            a = self.exec(n.l, env)
            return a if self._truthy(a) else self.exec(n.r, env)
        a = self.exec(n.l, env)
        b = self.exec(n.r, env)
        op = n.op
        if op == "+": return a + b
        if op == "-": return a - b
        if op == "*": return a * b
        if op == "/": return a / b
        if op == "%": return a % b
        if op == "==": return a == b
        if op == "!=": return a != b
        if op == "<": return a < b
        if op == ">": return a > b
        if op == "<=": return a <= b
        if op == ">=": return a >= b
        raise RuntimeError(f"未知运算符: {op}")

    def exec_UnaryOp(self, n, env):
        v = self.exec(n.e, env)
        if n.op == "-": return -v
        if n.op == "+": return +v
        if n.op == "!": return not self._truthy(v)
        raise RuntimeError(f"未知一元运算符: {n.op}")

    @staticmethod
    def _truthy(v):
        if v is None or v is False or v == 0 or v == "":
            return False
        return True


def run_file(path):
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    tokens = tokenize(src)
    ast = Parser(tokens).parse()
    Interpreter().run(ast)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # 默认跑示例
        sample = os.path.join(os.path.dirname(__file__), "examples", "fib.ml")
        if os.path.exists(sample):
            run_file(sample)
        else:
            print("用法: python minilang.py <file.ml>")
    else:
        run_file(sys.argv[1])
