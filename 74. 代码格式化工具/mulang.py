# -*- coding: utf-8 -*-
"""
自定义编程语言（极简）
- 名字：μLang（micro lang）
- 语法目标：尽量直观、易实现
- 文法：
  program   := stmt*
  stmt      := let | assign | if | while | for | func | return | block | print | expr_stmt
  let       := "let" IDENT "=" expr
  assign    := IDENT "=" expr
  block     := "{" stmt* "}"
  if        := "if" expr block ( "else" (if|block) )?
  while     := "while" expr block
  for       := "for" IDENT "in" expr ".." expr block
  func      := "fn" IDENT "(" params? ")" block
  return    := "return" expr?
  print     := "print" "(" args? ")"
  expr      := 逻辑/比较/算术 + 调用/索引/字面量
  字面量    := int | float | string | true | false | null | "[" args? "]" | IDENT

特性：变量、控制流、函数（带闭包）、列表、字符串拼接、print
实现：词法 + 递归下降 + 树遍历解释器

用法：
    python mulang.py             # REPL
    python mulang.py prog.ml     # 执行文件
"""
import sys
from pathlib import Path


# ---------- 词法 ----------
KEYWORDS = {"let", "if", "else", "while", "for", "in", "fn", "return",
            "true", "false", "null", "print", "and", "or", "not"}


class Tok:
    __slots__ = ("t", "v", "line")
    def __init__(self, t, v, line): self.t, self.v, self.line = t, v, line
    def __repr__(self): return f"<{self.t}:{self.v}@{self.line}>"


def tokenize(src):
    tokens, i, n, line = [], 0, len(src), 1
    while i < n:
        c = src[i]
        if c == "\n": line += 1; i += 1; continue
        if c in " \t\r": i += 1; continue
        if c == "#" or (c == "/" and i + 1 < n and src[i + 1] == "/"):
            while i < n and src[i] != "\n": i += 1
            continue
        if c.isdigit():
            j = i; dot = False
            while j < n and src[j].isdigit():
                j += 1
            if j < n and src[j] == "." and j + 1 < n and src[j + 1].isdigit():
                dot = True; j += 1
                while j < n and src[j].isdigit():
                    j += 1
            text = src[i:j]
            tokens.append(Tok("NUM", float(text) if dot else int(text), line))
            i = j; continue
        if c in "'\"":
            q = c; j = i + 1; out = []
            while j < n and src[j] != q:
                if src[j] == "\\" and j + 1 < n:
                    esc = src[j + 1]
                    out.append({"n": "\n", "t": "\t", "\\": "\\",
                                "'": "'", '"': '"'}.get(esc, esc))
                    j += 2
                else:
                    out.append(src[j]); j += 1
            if j >= n: raise SyntaxError(f"行 {line}: 未闭合字符串")
            tokens.append(Tok("STR", "".join(out), line))
            i = j + 1; continue
        if c.isalpha() or c == "_":
            j = i + 1
            while j < n and (src[j].isalnum() or src[j] == "_"): j += 1
            text = src[i:j]
            if text in KEYWORDS:
                tokens.append(Tok("KW", text, line))
            else:
                tokens.append(Tok("ID", text, line))
            i = j; continue
        two = src[i:i + 2]
        if two in ("==", "!=", "<=", ">=", "&&", "||", ".."):
            tokens.append(Tok("OP", two, line)); i += 2; continue
        if c in "+-*/%=<>(){}[],;":
            tokens.append(Tok("OP", c, line)); i += 1; continue
        raise SyntaxError(f"行 {line}: 非法字符 {c!r}")
    tokens.append(Tok("EOF", None, line))
    return tokens


# ---------- AST ----------
class N: pass
class NLit(N):
    def __init__(self, v): self.v = v
class NList(N):
    def __init__(self, items): self.items = items
class NVar(N):
    def __init__(self, name): self.name = name
class NLet(N):
    def __init__(self, name, e): self.name, self.e = name, e
class NAssign(N):
    def __init__(self, name, e): self.name, self.e = name, e
class NBin(N):
    def __init__(self, op, l, r): self.op, self.l, self.r = op, l, r
class NUna(N):
    def __init__(self, op, e): self.op, self.e = op, e
class NIf(N):
    def __init__(self, cond, then, els): self.cond, self.then, self.els = cond, then, els
class NWhile(N):
    def __init__(self, cond, body): self.cond, self.body = cond, body
class NFor(N):
    def __init__(self, var, lo, hi, body): self.var, self.lo, self.hi, self.body = var, lo, hi, body
class NBlock(N):
    def __init__(self, stmts): self.stmts = stmts
class NFunc(N):
    def __init__(self, name, params, body): self.name, self.params, self.body = name, params, body
class NCall(N):
    def __init__(self, fn, args): self.fn, self.args = fn, args
class NReturn(N):
    def __init__(self, e): self.e = e
class NPrint(N):
    def __init__(self, args): self.args = args
class NIndex(N):
    def __init__(self, obj, idx): self.obj, self.idx = obj, idx


# ---------- 解析 ----------
class Parser:
    def __init__(self, toks): self.toks = toks; self.p = 0

    def peek(self, k=0): return self.toks[self.p + k]
    def at(self, t, v=None):
        tk = self.peek()
        return tk.t == t and (v is None or tk.v == v)
    def eat(self, t=None, v=None):
        tk = self.toks[self.p]
        if t and tk.t != t: raise SyntaxError(f"行 {tk.line}: 期待 {t}, 实得 {tk}")
        if v is not None and tk.v != v: raise SyntaxError(f"行 {tk.line}: 期待 {v!r}, 实得 {tk.v!r}")
        self.p += 1; return tk

    def parse(self):
        stmts = []
        while not self.at("EOF"):
            stmts.append(self.parse_stmt())
            while self.at("OP", ";"): self.eat()
        return NBlock(stmts)

    def parse_stmt(self):
        if self.at("KW", "let"):
            self.eat(); name = self.eat("ID").v
            self.eat("OP", "="); e = self.parse_expr()
            return NLet(name, e)
        if self.at("KW", "if"):
            return self.parse_if()
        if self.at("KW", "while"):
            self.eat(); cond = self.parse_expr(); body = self.parse_block()
            return NWhile(cond, body)
        if self.at("KW", "for"):
            self.eat(); var = self.eat("ID").v
            self.eat("KW", "in")
            lo = self.parse_expr()
            self.eat("OP", "..")
            hi = self.parse_expr()
            body = self.parse_block()
            return NFor(var, lo, hi, body)
        if self.at("KW", "fn"):
            self.eat(); name = self.eat("ID").v
            self.eat("OP", "(")
            params = []
            if not self.at("OP", ")"):
                params.append(self.eat("ID").v)
                while self.at("OP", ","):
                    self.eat(); params.append(self.eat("ID").v)
            self.eat("OP", ")")
            body = self.parse_block()
            return NFunc(name, params, body)
        if self.at("KW", "return"):
            self.eat()
            if self.at("OP", "}") or self.at("OP", ";") or self.at("EOF"):
                return NReturn(NLit(None))
            return NReturn(self.parse_expr())
        if self.at("KW", "print"):
            self.eat(); self.eat("OP", "(")
            args = []
            if not self.at("OP", ")"):
                args.append(self.parse_expr())
                while self.at("OP", ","):
                    self.eat(); args.append(self.parse_expr())
            self.eat("OP", ")")
            return NPrint(args)
        if self.at("OP", "{"):
            return self.parse_block()
        # 赋值或表达式
        if self.at("ID") and self.toks[self.p + 1].t == "OP" and self.toks[self.p + 1].v == "=":
            name = self.eat("ID").v
            self.eat("OP", "=")
            return NAssign(name, self.parse_expr())
        return self.parse_expr()

    def parse_if(self):
        self.eat("KW", "if")
        cond = self.parse_expr()
        then = self.parse_block()
        els = None
        if self.at("KW", "else"):
            self.eat()
            if self.at("KW", "if"):
                els = self.parse_if()
            else:
                els = self.parse_block()
        return NIf(cond, then, els)

    def parse_block(self):
        self.eat("OP", "{")
        stmts = []
        while not self.at("OP", "}"):
            stmts.append(self.parse_stmt())
            while self.at("OP", ";"): self.eat()
        self.eat("OP", "}")
        return NBlock(stmts)

    # 表达式优先级
    def parse_expr(self): return self.parse_or()
    def parse_or(self):
        l = self.parse_and()
        while (self.at("KW", "or") or self.at("OP", "||")):
            self.eat(); l = NBin("or", l, self.parse_and())
        return l
    def parse_and(self):
        l = self.parse_not()
        while (self.at("KW", "and") or self.at("OP", "&&")):
            self.eat(); l = NBin("and", l, self.parse_not())
        return l
    def parse_not(self):
        if self.at("KW", "not"):
            self.eat(); return NUna("not", self.parse_not())
        return self.parse_eq()
    def parse_eq(self):
        l = self.parse_cmp()
        while self.at("OP") and self.peek().v in ("==", "!="):
            op = self.eat().v; l = NBin(op, l, self.parse_cmp())
        return l
    def parse_cmp(self):
        l = self.parse_add()
        while self.at("OP") and self.peek().v in ("<", "<=", ">", ">="):
            op = self.eat().v; l = NBin(op, l, self.parse_add())
        return l
    def parse_add(self):
        l = self.parse_mul()
        while self.at("OP") and self.peek().v in ("+", "-"):
            op = self.eat().v; l = NBin(op, l, self.parse_mul())
        return l
    def parse_mul(self):
        l = self.parse_unary()
        while self.at("OP") and self.peek().v in ("*", "/", "%"):
            op = self.eat().v; l = NBin(op, l, self.parse_unary())
        return l
    def parse_unary(self):
        if self.at("OP") and self.peek().v in ("+", "-"):
            op = self.eat().v; return NUna(op, self.parse_unary())
        return self.parse_postfix()
    def parse_postfix(self):
        e = self.parse_primary()
        while True:
            if self.at("OP", "("):
                self.eat(); args = []
                if not self.at("OP", ")"):
                    args.append(self.parse_expr())
                    while self.at("OP", ","):
                        self.eat(); args.append(self.parse_expr())
                self.eat("OP", ")"); e = NCall(e, args)
            elif self.at("OP", "["):
                self.eat(); idx = self.parse_expr(); self.eat("OP", "]")
                e = NIndex(e, idx)
            else:
                break
        return e
    def parse_primary(self):
        t = self.peek()
        if t.t == "NUM": self.eat(); return NLit(t.v)
        if t.t == "STR": self.eat(); return NLit(t.v)
        if t.t == "KW" and t.v in ("true", "false"): self.eat(); return NLit(t.v == "true")
        if t.t == "KW" and t.v == "null": self.eat(); return NLit(None)
        if t.t == "OP" and t.v == "(":
            self.eat(); e = self.parse_expr(); self.eat("OP", ")"); return e
        if t.t == "OP" and t.v == "[":
            self.eat(); items = []
            if not self.at("OP", "]"):
                items.append(self.parse_expr())
                while self.at("OP", ","):
                    self.eat(); items.append(self.parse_expr())
            self.eat("OP", "]"); return NList(items)
        if t.t == "ID":
            self.eat(); return NVar(t.v)
        raise SyntaxError(f"行 {t.line}: 非预期 {t}")


# ---------- 解释器 ----------
class Env:
    def __init__(self, parent=None): self.vars = {}; self.parent = parent
    def get(self, name):
        if name in self.vars: return self.vars[name]
        if self.parent: return self.parent.get(name)
        raise NameError(name)
    def set(self, name, value):
        if name in self.vars: self.vars[name] = value; return
        if self.parent and self._has_in_parent(name):
            self.parent.set(name, value); return
        raise NameError(f"未定义 {name}（请先 let）")
    def _has_in_parent(self, name):
        e = self.parent
        while e is not None:
            if name in e.vars: return True
            e = e.parent
        return False
    def declare(self, name, value): self.vars[name] = value
    def has(self, name):
        return name in self.vars or (self.parent.has(name) if self.parent else False)


class Function:
    def __init__(self, params, body, closure):
        self.params, self.body, self.closure = params, body, closure


class ReturnSignal(Exception):
    def __init__(self, value): self.value = value


BUILTINS = {
    "len": len, "str": str, "int": int, "float": float, "bool": bool,
    "abs": abs, "min": min, "max": max,
    "push": lambda lst, x: lst.append(x) or lst,
    "pop": lambda lst: lst.pop(),
    "range": lambda a, b: list(range(a, b)),
    "input": input,
}


class Interpreter:
    def __init__(self):
        self.globals = Env()
        for k, v in BUILTINS.items():
            self.globals.declare(k, v)

    def run(self, src):
        toks = tokenize(src)
        ast = Parser(toks).parse()
        return self.exec_block(ast, self.globals)

    def exec_block(self, block, env):
        result = None
        for s in block.stmts:
            result = self.exec(s, env)
        return result

    def exec(self, node, env):
        m = getattr(self, f"e_{type(node).__name__}")
        return m(node, env)

    def e_NLit(self, n, env): return n.v
    def e_NList(self, n, env): return [self.exec(x, env) for x in n.items]
    def e_NVar(self, n, env): return env.get(n.name)
    def e_NLet(self, n, env): env.declare(n.name, self.exec(n.e, env))
    def e_NAssign(self, n, env):
        val = self.exec(n.e, env); env.set(n.name, val); return val
    def e_NUna(self, n, env):
        v = self.exec(n.e, env)
        if n.op == "-": return -v
        if n.op == "+": return +v
        if n.op == "not": return not v
    def e_NBin(self, n, env):
        if n.op == "and":
            l = self.exec(n.l, env); return self.exec(n.r, env) if l else l
        if n.op == "or":
            l = self.exec(n.l, env); return l if l else self.exec(n.r, env)
        a, b = self.exec(n.l, env), self.exec(n.r, env)
        if n.op == "+": return a + b
        if n.op == "-": return a - b
        if n.op == "*": return a * b
        if n.op == "/": return a / b
        if n.op == "%": return a % b
        if n.op == "==": return a == b
        if n.op == "!=": return a != b
        if n.op == "<":  return a < b
        if n.op == "<=": return a <= b
        if n.op == ">":  return a > b
        if n.op == ">=": return a >= b
    def e_NIf(self, n, env):
        if self.exec(n.cond, env):
            return self.exec(n.then, env)
        elif n.els is not None:
            return self.exec(n.els, env)
    def e_NWhile(self, n, env):
        while self.exec(n.cond, env):
            self.exec(n.body, env)
    def e_NFor(self, n, env):
        lo = self.exec(n.lo, env); hi = self.exec(n.hi, env)
        scope = Env(env); scope.declare(n.var, lo)
        for i in range(int(lo), int(hi)):
            scope.vars[n.var] = i
            self.exec(n.body, scope)
    def e_NBlock(self, n, env):
        scope = Env(env)
        return self.exec_block(n, scope)
    def e_NFunc(self, n, env):
        fn = Function(n.params, n.body, env)
        env.declare(n.name, fn)
    def e_NReturn(self, n, env):
        raise ReturnSignal(self.exec(n.e, env))
    def e_NPrint(self, n, env):
        vals = [self.exec(a, env) for a in n.args]
        print(*[self._fmt(v) for v in vals])
    def e_NIndex(self, n, env):
        obj = self.exec(n.obj, env); idx = self.exec(n.idx, env)
        return obj[int(idx)] if isinstance(obj, list) else obj[idx]
    def e_NCall(self, n, env):
        fn = self.exec(n.fn, env)
        args = [self.exec(a, env) for a in n.args]
        if isinstance(fn, Function):
            scope = Env(fn.closure)
            for p, v in zip(fn.params, args):
                scope.declare(p, v)
            try:
                self.exec(fn.body, scope)
            except ReturnSignal as r:
                return r.value
            return None
        if callable(fn):
            return fn(*args)
        raise TypeError("不可调用")

    @staticmethod
    def _fmt(v):
        if v is True: return "true"
        if v is False: return "false"
        if v is None: return "null"
        return v


# ---------- main / REPL ----------
def repl():
    interp = Interpreter()
    print("μLang REPL — :q 退出")
    buf = ""
    while True:
        try:
            prompt = "μ> " if not buf else ".. "
            line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print(); break
        if line.strip() in (":q", "exit"): break
        buf += line + "\n"
        # 简单判断括号配平
        if buf.count("{") > buf.count("}"):
            continue
        try:
            r = interp.run(buf)
            if r is not None:
                print(Interpreter._fmt(r))
        except Exception as e:
            print(f"[err] {e}")
        buf = ""


def main():
    if len(sys.argv) > 1:
        src = Path(sys.argv[1]).read_text(encoding="utf-8")
        Interpreter().run(src)
    else:
        repl()


if __name__ == "__main__":
    main()
