"""
PyLang - 纯 Python 实现的编程语言解释器（支持函数 / 闭包 / 高阶函数）
==========================================================================

这是一门小型动态语言「PyLang」的实现。语言特性：

  - 数据类型：number / string / bool / nil / list / 函数
  - 变量：let x = expr;
  - 函数：fn name(a, b) { ... return ...; }    // 一等公民、词法作用域、可嵌套
  - 匿名函数（lambda）：fn(a, b) { return a + b; }
  - 控制流：if (...) { ... } else { ... }, while (...) { ... }, for (let i=0; i<n; i=i+1) { ... }
  - 表达式：算术 +-*/%, 比较 ==!=<<=>>=, 逻辑 && || !
  - 字符串拼接：+, 索引 s[i]
  - 列表字面量：[1, 2, 3]，索引 a[i]
  - 内置：print, len, push, pop, str, num, type, time

实现采用经典「Lexer -> Parser -> Tree-Walking Interpreter」三段式。
仅依赖 Python 标准库。

用法
----
    python pylang.py demo                # 一键执行内置示例
    python pylang.py run script.pl       # 执行脚本
    python pylang.py repl                # 交互式 REPL
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from typing import Any


# ============================================================================
# 1. Lexer
# ============================================================================
KEYWORDS = {
    "let", "fn", "return", "if", "else", "while", "for",
    "true", "false", "nil", "break", "continue",
}
SINGLE = "+-*/%(){}[];,"
DOUBLE = {"==", "!=", "<=", ">=", "&&", "||"}


class Token:
    __slots__ = ("kind", "value", "line")

    def __init__(self, kind: str, value: Any, line: int):
        self.kind = kind
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Tok({self.kind}, {self.value!r})"


def tokenize(src: str) -> list[Token]:
    out: list[Token] = []
    i = 0
    line = 1
    n = len(src)
    while i < n:
        c = src[i]
        if c == "\n":
            line += 1
            i += 1
            continue
        if c.isspace():
            i += 1
            continue
        if c == "/" and i + 1 < n and src[i + 1] == "/":
            while i < n and src[i] != "\n":
                i += 1
            continue
        if c == '"':
            j = i + 1
            buf = []
            while j < n and src[j] != '"':
                if src[j] == "\\" and j + 1 < n:
                    esc = src[j + 1]
                    buf.append({"n": "\n", "t": "\t", "\\": "\\", '"': '"'}.get(esc, esc))
                    j += 2
                else:
                    buf.append(src[j])
                    j += 1
            if j >= n:
                raise SyntaxError(f"unterminated string at line {line}")
            out.append(Token("STR", "".join(buf), line))
            i = j + 1
            continue
        if c.isdigit():
            j = i
            while j < n and (src[j].isdigit() or src[j] == "."):
                j += 1
            num_s = src[i:j]
            num: Any = float(num_s) if "." in num_s else int(num_s)
            out.append(Token("NUM", num, line))
            i = j
            continue
        if c.isalpha() or c == "_":
            j = i
            while j < n and (src[j].isalnum() or src[j] == "_"):
                j += 1
            ident = src[i:j]
            if ident in KEYWORDS:
                out.append(Token(ident, ident, line))
            else:
                out.append(Token("ID", ident, line))
            i = j
            continue
        if i + 1 < n and src[i:i + 2] in DOUBLE:
            out.append(Token(src[i:i + 2], src[i:i + 2], line))
            i += 2
            continue
        if c in "<>=!":
            out.append(Token(c, c, line))
            i += 1
            continue
        if c in SINGLE:
            out.append(Token(c, c, line))
            i += 1
            continue
        raise SyntaxError(f"unexpected char {c!r} at line {line}")
    out.append(Token("EOF", None, line))
    return out


# ============================================================================
# 2. AST
# ============================================================================
@dataclass
class Num:    value: Any
@dataclass
class Str:    value: str
@dataclass
class Bool:   value: bool
@dataclass
class Nil:    pass
@dataclass
class Var:    name: str
@dataclass
class List_:  items: list
@dataclass
class Index:  obj: Any; idx: Any
@dataclass
class BinOp:  op: str; left: Any; right: Any
@dataclass
class UnaryOp: op: str; operand: Any
@dataclass
class Call:   func: Any; args: list
@dataclass
class FnLit:  params: list[str]; body: list      # anonymous
@dataclass
class Assign: target: Any; value: Any            # target: Var or Index
@dataclass
class Let:    name: str; value: Any
@dataclass
class FnDecl: name: str; params: list[str]; body: list
@dataclass
class If:     cond: Any; then: list; els: list
@dataclass
class While:  cond: Any; body: list
@dataclass
class For:    init: Any; cond: Any; step: Any; body: list
@dataclass
class Return: value: Any
@dataclass
class Break:  pass
@dataclass
class Continue: pass
@dataclass
class ExprStmt: value: Any


# ============================================================================
# 3. Parser
# ============================================================================
class Parser:
    def __init__(self, toks: list[Token]):
        self.t = toks
        self.i = 0

    def peek(self, o: int = 0) -> Token:
        return self.t[self.i + o]

    def eat(self, *kinds: str) -> Token:
        tk = self.t[self.i]
        if kinds and tk.kind not in kinds:
            raise SyntaxError(f"expected {kinds}, got {tk.kind}({tk.value!r}) at line {tk.line}")
        self.i += 1
        return tk

    def accept(self, *kinds: str) -> Token | None:
        if self.t[self.i].kind in kinds:
            return self.eat()
        return None

    # ------------------------------------------------------------------
    def parse_program(self) -> list:
        stmts = []
        while self.peek().kind != "EOF":
            stmts.append(self.parse_stmt())
        return stmts

    def parse_stmt(self):
        k = self.peek().kind
        if k == "let":
            return self.parse_let()
        if k == "fn" and self.peek(1).kind == "ID":
            return self.parse_fndecl()
        if k == "if":
            return self.parse_if()
        if k == "while":
            return self.parse_while()
        if k == "for":
            return self.parse_for()
        if k == "return":
            self.eat()
            val = None if self.peek().kind == ";" else self.parse_expr()
            self.eat(";")
            return Return(val if val is not None else Nil())
        if k == "break":
            self.eat(); self.eat(";"); return Break()
        if k == "continue":
            self.eat(); self.eat(";"); return Continue()
        if k == "{":
            # bare block -> wrap as if(true)
            return If(Bool(True), self.parse_block(), [])
        e = self.parse_expr()
        self.eat(";")
        return ExprStmt(e)

    def parse_let(self):
        self.eat("let")
        name = self.eat("ID").value
        self.eat("=")
        val = self.parse_expr()
        self.eat(";")
        return Let(name, val)

    def parse_fndecl(self):
        self.eat("fn")
        name = self.eat("ID").value
        params = self.parse_params()
        body = self.parse_block()
        return FnDecl(name, params, body)

    def parse_params(self) -> list[str]:
        self.eat("(")
        ps: list[str] = []
        if self.peek().kind != ")":
            ps.append(self.eat("ID").value)
            while self.accept(","):
                ps.append(self.eat("ID").value)
        self.eat(")")
        return ps

    def parse_block(self) -> list:
        self.eat("{")
        stmts = []
        while self.peek().kind != "}":
            stmts.append(self.parse_stmt())
        self.eat("}")
        return stmts

    def parse_if(self):
        self.eat("if")
        self.eat("(")
        cond = self.parse_expr()
        self.eat(")")
        then = self.parse_block()
        els = []
        if self.accept("else"):
            if self.peek().kind == "if":
                els = [self.parse_if()]
            else:
                els = self.parse_block()
        return If(cond, then, els)

    def parse_while(self):
        self.eat("while")
        self.eat("(")
        cond = self.parse_expr()
        self.eat(")")
        body = self.parse_block()
        return While(cond, body)

    def parse_for(self):
        self.eat("for")
        self.eat("(")
        init = self.parse_let() if self.peek().kind == "let" else self._for_expr_stmt()
        cond = self.parse_expr()
        self.eat(";")
        step = self.parse_expr()
        self.eat(")")
        body = self.parse_block()
        return For(init, cond, step, body)

    def _for_expr_stmt(self):
        e = self.parse_expr()
        self.eat(";")
        return ExprStmt(e)

    # --------- expressions: precedence climbing ----------
    PREC = {
        "||": 1, "&&": 2,
        "==": 3, "!=": 3,
        "<": 4, "<=": 4, ">": 4, ">=": 4,
        "+": 5, "-": 5,
        "*": 6, "/": 6, "%": 6,
    }

    def parse_expr(self):
        return self.parse_assign()

    def parse_assign(self):
        left = self.parse_binop(1)
        if self.accept("="):
            right = self.parse_assign()
            if not isinstance(left, (Var, Index)):
                raise SyntaxError("invalid assignment target")
            return Assign(left, right)
        return left

    def parse_binop(self, min_prec: int):
        left = self.parse_unary()
        while True:
            tk = self.peek()
            prec = self.PREC.get(tk.kind, 0)
            if prec < min_prec:
                break
            op = self.eat().kind
            right = self.parse_binop(prec + 1)
            left = BinOp(op, left, right)
        return left

    def parse_unary(self):
        if self.accept("-"):
            return UnaryOp("-", self.parse_unary())
        if self.accept("!"):
            return UnaryOp("!", self.parse_unary())
        return self.parse_postfix()

    def parse_postfix(self):
        node = self.parse_primary()
        while True:
            if self.accept("("):
                args = []
                if self.peek().kind != ")":
                    args.append(self.parse_expr())
                    while self.accept(","):
                        args.append(self.parse_expr())
                self.eat(")")
                node = Call(node, args)
            elif self.accept("["):
                idx = self.parse_expr()
                self.eat("]")
                node = Index(node, idx)
            else:
                break
        return node

    def parse_primary(self):
        tk = self.peek()
        if tk.kind == "NUM":
            self.eat(); return Num(tk.value)
        if tk.kind == "STR":
            self.eat(); return Str(tk.value)
        if tk.kind == "true":
            self.eat(); return Bool(True)
        if tk.kind == "false":
            self.eat(); return Bool(False)
        if tk.kind == "nil":
            self.eat(); return Nil()
        if tk.kind == "ID":
            self.eat(); return Var(tk.value)
        if tk.kind == "(":
            self.eat()
            e = self.parse_expr()
            self.eat(")")
            return e
        if tk.kind == "[":
            self.eat()
            items = []
            if self.peek().kind != "]":
                items.append(self.parse_expr())
                while self.accept(","):
                    items.append(self.parse_expr())
            self.eat("]")
            return List_(items)
        if tk.kind == "fn":
            self.eat("fn")
            params = self.parse_params()
            body = self.parse_block()
            return FnLit(params, body)
        raise SyntaxError(f"unexpected token {tk.kind}({tk.value!r}) at line {tk.line}")


# ============================================================================
# 4. Environment + Function values
# ============================================================================
class Env:
    def __init__(self, parent: "Env | None" = None):
        self.parent = parent
        self.vars: dict[str, Any] = {}

    def define(self, name: str, value: Any):
        self.vars[name] = value

    def get(self, name: str):
        if name in self.vars:
            return self.vars[name]
        if self.parent is not None:
            return self.parent.get(name)
        raise NameError(f"undefined variable: {name}")

    def set(self, name: str, value: Any):
        if name in self.vars:
            self.vars[name] = value
            return
        if self.parent is not None:
            self.parent.set(name, value)
            return
        raise NameError(f"assign to undefined variable: {name}")


@dataclass
class Function:
    params: list[str]
    body: list
    closure: Env
    name: str = ""

    def __repr__(self):
        return f"<fn {self.name or 'lambda'}/{len(self.params)}>"


@dataclass
class Builtin:
    name: str
    fn: Any
    def __repr__(self):
        return f"<builtin {self.name}>"


# ============================================================================
# 5. Interpreter (tree-walking)
# ============================================================================
class _ReturnSignal(Exception):
    def __init__(self, value): self.value = value
class _BreakSignal(Exception): pass
class _ContinueSignal(Exception): pass


def builtin_print(*args):
    print(*[_format(a) for a in args])
    return None


def _format(v: Any) -> str:
    if v is None:
        return "nil"
    if v is True:
        return "true"
    if v is False:
        return "false"
    if isinstance(v, list):
        return "[" + ", ".join(_format(x) for x in v) + "]"
    return str(v)


def builtin_len(x):
    if x is None:
        return 0
    return len(x)


def builtin_push(lst, v):
    if not isinstance(lst, list):
        raise TypeError("push: first arg must be list")
    lst.append(v)
    return lst


def builtin_pop(lst):
    if not isinstance(lst, list) or not lst:
        return None
    return lst.pop()


def builtin_str(x):
    return _format(x)


def builtin_num(x):
    if isinstance(x, (int, float)):
        return x
    try:
        return int(x)
    except (ValueError, TypeError):
        try:
            return float(x)
        except (ValueError, TypeError):
            return None


def builtin_type(x):
    if x is None: return "nil"
    if isinstance(x, bool): return "bool"
    if isinstance(x, int): return "number"
    if isinstance(x, float): return "number"
    if isinstance(x, str): return "string"
    if isinstance(x, list): return "list"
    if isinstance(x, (Function, Builtin)): return "function"
    return "unknown"


GLOBAL_BUILTINS = {
    "print": Builtin("print", builtin_print),
    "len":   Builtin("len", builtin_len),
    "push":  Builtin("push", builtin_push),
    "pop":   Builtin("pop", builtin_pop),
    "str":   Builtin("str", builtin_str),
    "num":   Builtin("num", builtin_num),
    "type":  Builtin("type", builtin_type),
    "time":  Builtin("time", lambda: time.time()),
}


class Interpreter:
    def __init__(self):
        self.globals = Env()
        for k, v in GLOBAL_BUILTINS.items():
            self.globals.define(k, v)

    def run(self, src: str):
        toks = tokenize(src)
        prog = Parser(toks).parse_program()
        for stmt in prog:
            self.exec_stmt(stmt, self.globals)

    # ----------------------------- exec stmt ------------------------------
    def exec_stmt(self, s, env: Env):
        if isinstance(s, Let):
            env.define(s.name, self.eval(s.value, env))
        elif isinstance(s, FnDecl):
            env.define(s.name, Function(s.params, s.body, env, s.name))
        elif isinstance(s, ExprStmt):
            self.eval(s.value, env)
        elif isinstance(s, If):
            if _truthy(self.eval(s.cond, env)):
                self.exec_block(s.then, env)
            else:
                self.exec_block(s.els, env)
        elif isinstance(s, While):
            while _truthy(self.eval(s.cond, env)):
                try:
                    self.exec_block(s.body, env)
                except _BreakSignal:
                    break
                except _ContinueSignal:
                    continue
        elif isinstance(s, For):
            scope = Env(env)
            self.exec_stmt(s.init, scope)
            while _truthy(self.eval(s.cond, scope)):
                try:
                    self.exec_block(s.body, scope)
                except _BreakSignal:
                    break
                except _ContinueSignal:
                    pass
                self.eval(s.step, scope)
        elif isinstance(s, Return):
            raise _ReturnSignal(self.eval(s.value, env))
        elif isinstance(s, Break):
            raise _BreakSignal()
        elif isinstance(s, Continue):
            raise _ContinueSignal()
        else:
            raise RuntimeError(f"bad stmt: {s}")

    def exec_block(self, stmts: list, env: Env):
        scope = Env(env)
        for s in stmts:
            self.exec_stmt(s, scope)

    # ----------------------------- eval expr ------------------------------
    def eval(self, e, env: Env):
        if isinstance(e, Num):  return e.value
        if isinstance(e, Str):  return e.value
        if isinstance(e, Bool): return e.value
        if isinstance(e, Nil):  return None
        if isinstance(e, Var):  return env.get(e.name)
        if isinstance(e, List_):
            return [self.eval(x, env) for x in e.items]
        if isinstance(e, FnLit):
            return Function(e.params, e.body, env)
        if isinstance(e, UnaryOp):
            v = self.eval(e.operand, env)
            if e.op == "-":
                return -v
            if e.op == "!":
                return not _truthy(v)
        if isinstance(e, BinOp):
            return self._binop(e, env)
        if isinstance(e, Index):
            obj = self.eval(e.obj, env)
            idx = self.eval(e.idx, env)
            return obj[int(idx)] if isinstance(obj, (list, str)) else None
        if isinstance(e, Assign):
            val = self.eval(e.value, env)
            if isinstance(e.target, Var):
                # 优先就地更新 (允许在外层赋值);若不存在,定义到当前作用域
                try:
                    env.set(e.target.name, val)
                except NameError:
                    env.define(e.target.name, val)
            elif isinstance(e.target, Index):
                obj = self.eval(e.target.obj, env)
                idx = self.eval(e.target.idx, env)
                obj[int(idx)] = val
            return val
        if isinstance(e, Call):
            f = self.eval(e.func, env)
            args = [self.eval(a, env) for a in e.args]
            return self.call(f, args)
        raise RuntimeError(f"bad expr: {e}")

    def _binop(self, e: BinOp, env: Env):
        # short-circuit for &&/||
        if e.op == "&&":
            a = self.eval(e.left, env)
            return self.eval(e.right, env) if _truthy(a) else a
        if e.op == "||":
            a = self.eval(e.left, env)
            return a if _truthy(a) else self.eval(e.right, env)
        a = self.eval(e.left, env)
        b = self.eval(e.right, env)
        op = e.op
        if op == "+":
            if isinstance(a, str) or isinstance(b, str):
                return _format(a) + _format(b)
            return a + b
        if op == "-": return a - b
        if op == "*":
            if isinstance(a, str) and isinstance(b, int):
                return a * b
            return a * b
        if op == "/":
            if isinstance(a, int) and isinstance(b, int) and b != 0:
                return a // b if (a % b == 0) else a / b
            return a / b
        if op == "%": return a % b
        if op == "==": return a == b
        if op == "!=": return a != b
        if op == "<":  return a < b
        if op == "<=": return a <= b
        if op == ">":  return a > b
        if op == ">=": return a >= b
        raise RuntimeError(f"bad binop {op}")

    def call(self, f, args: list):
        if isinstance(f, Builtin):
            return f.fn(*args)
        if isinstance(f, Function):
            if len(args) != len(f.params):
                raise TypeError(f"{f.name or 'lambda'} expects {len(f.params)} args, got {len(args)}")
            scope = Env(f.closure)
            for n, v in zip(f.params, args):
                scope.define(n, v)
            try:
                for s in f.body:
                    self.exec_stmt(s, scope)
            except _ReturnSignal as r:
                return r.value
            return None
        raise TypeError(f"not callable: {f!r}")


def _truthy(v: Any) -> bool:
    if v is None or v is False or v == 0 or v == "":
        return False
    return True


# ============================================================================
# 6. CLI / demo
# ============================================================================
DEMO_PROG = r"""
// PyLang 演示

print("== arithmetic ==");
print(1 + 2 * 3);          // 7
print((1 + 2) * 3);        // 9
print(10 % 3);             // 1

print("== strings ==");
let s = "hello" + ", " + "world";
print(s);
print(len(s));

print("== conditionals ==");
let n = 7;
if (n % 2 == 0) { print("even"); } else { print("odd"); }

print("== loops ==");
let sum = 0;
for (let i = 1; i <= 10; i = i + 1) {
    sum = sum + i;
}
print("1..10 sum =", sum);

print("== functions + recursion ==");
fn fact(n) {
    if (n <= 1) { return 1; }
    return n * fact(n - 1);
}
print("10! =", fact(10));

fn fib(n) {
    if (n < 2) { return n; }
    return fib(n-1) + fib(n-2);
}
print("fib(15) =", fib(15));

print("== closures ==");
fn make_adder(x) {
    return fn(y) { return x + y; };
}
let add10 = make_adder(10);
print(add10(5));
print(add10(7));

print("== higher-order ==");
fn map(arr, f) {
    let out = [];
    for (let i = 0; i < len(arr); i = i + 1) {
        push(out, f(arr[i]));
    }
    return out;
}
let xs = [1, 2, 3, 4, 5];
let ys = map(xs, fn(v) { return v * v; });
print(ys);

print("== mutate list ==");
let a = [10, 20, 30];
a[1] = 99;
push(a, 40);
print(a, "len=", len(a));

print("== counter via closure ==");
fn counter() {
    let n = 0;
    return fn() { n = n + 1; return n; };
}
let c = counter();
print(c(), c(), c());
"""


def repl():
    interp = Interpreter()
    print("PyLang REPL. Ctrl+C to quit. Multi-line input ends with empty line.")
    buf = []
    while True:
        try:
            prompt = "pl> " if not buf else "... "
            line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if line == "" and buf:
            src = "\n".join(buf)
            buf = []
            try:
                # 单表达式自动 print
                if not src.rstrip().endswith(";") and "\n" not in src:
                    interp.run(f"print({src});")
                else:
                    interp.run(src)
            except Exception as e:  # noqa: BLE001
                print(f"error: {e}")
        elif line:
            buf.append(line)


def main():
    if len(sys.argv) < 2 or sys.argv[1] == "demo":
        Interpreter().run(DEMO_PROG)
        return
    if sys.argv[1] == "repl":
        repl()
        return
    if sys.argv[1] == "run" and len(sys.argv) >= 3:
        src = open(sys.argv[2], encoding="utf-8").read()
        Interpreter().run(src)
        return
    print("usage: pylang.py demo | repl | run <file>")


if __name__ == "__main__":
    main()
